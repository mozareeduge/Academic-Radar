"""Research service: runs workflow and persists results to database."""

import os
import sys
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session

from academic_radar.research.graph import build_graph
from academic_radar.research.protocol_loader import load_protocols
from academic_radar.research.run_identity import make_run_identity
from academic_radar.domain.enums import ResearchState, CoverageStatus, ClaimStatus, can_transition
from academic_radar.domain.invalidation import add_dependency
from db.radar_models_cases import EvaluationCase
from db.radar_models_evidence import ResearchRun, ResearchCoverage, SourceSnapshot, EvidenceArtifact
from db.radar_models_claims import Claim, ClaimEvidence

log = logging.getLogger(__name__)


def run_research(
    session: Session,
    case_id: str,
    provider,
    evidence_lookup: dict,
    run_key: Optional[str] = None,
) -> str:
    """Run research workflow and persist results in one transaction.

    Args:
        session: SQLAlchemy session (must be committed by caller)
        case_id: The evaluation case ID
        provider: LLM provider with complete(messages, schema_name) method
        evidence_lookup: Dict mapping evidence_id -> evidence details
        run_key: Optional idempotency key (defaults to case_id)

    Returns:
        The research run ID

    Raises:
        ValueError: if case not found, protocol not found, or workflow fails validation
    """
    print(f"DEBUG SERVICE: run_research called for case {case_id}", file=sys.stderr, flush=True)
    run_key = run_key or case_id

    # Load case
    case = session.query(EvaluationCase).filter_by(id=case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")
    print(f"DEBUG SERVICE: Case found: {case.id}, state={case.research_state}", file=sys.stderr, flush=True)

    # Load protocol by application_route
    protocols = load_protocols()
    protocol_key = case.application_route
    if protocol_key not in protocols:
        raise ValueError(f"Protocol {protocol_key} not found")
    protocol = protocols[protocol_key]

    # Transition case state: DISCOVERED -> TRIAGED -> RESEARCHING
    current_state = ResearchState(case.research_state)
    if can_transition(current_state, ResearchState.TRIAGED):
        case.research_state = ResearchState.TRIAGED.value
    if can_transition(ResearchState(case.research_state), ResearchState.RESEARCHING):
        case.research_state = ResearchState.RESEARCHING.value

    # Build and run the workflow
    graph = build_graph(provider, protocol, evidence_lookup)
    initial_state = {
        "case_state": {"case_id": case_id},
        "sources": [],
    }
    result = graph.invoke(initial_state)
    print(f"DEBUG SERVICE: Graph result keys: {result.keys() if isinstance(result, dict) else type(result)}", file=sys.stderr, flush=True)
    print(f"DEBUG SERVICE: Claims in result: {result.get('claims', [])}", file=sys.stderr, flush=True)
    print(f"DEBUG SERVICE: Coverage in result: {list(result.get('coverage', {}).keys())}", file=sys.stderr, flush=True)

    # Determine run status based on readiness
    readiness = result.get("readiness", {})
    status = "COMPLETED" if readiness.get("ready") else "PARTIAL"

    # Create research run record
    run_id = _create_run_id()

    # Compute prompt hash from all nine node prompts for identity
    prompt_hash = _compute_prompt_hash()
    schema_version = "1.0.0"

    run = ResearchRun(
        id=run_id,
        case_id=case_id,
        protocol_version=protocol.version,
        model_id="mock-model",
        provider_id="mock-provider" if os.environ.get("RADAR_FIXTURE_MODE") == "1" else "llm-provider",
        prompt_hash=prompt_hash,
        schema_version=schema_version,
        run_identity={"run_key": run_key},
        status=status,
    )
    session.add(run)
    session.flush()
    print(f"DEBUG SERVICE: Created run record {run_id}", file=sys.stderr, flush=True)

    # Create coverage records
    coverage = result.get("coverage", {})

    # Add NOT_SEARCHED for missing mandatory classes
    for mandatory_class in protocol.mandatory:
        if mandatory_class not in coverage:
            coverage[mandatory_class] = CoverageStatus.NOT_SEARCHED

    for evidence_class, cov_status in coverage.items():
        cov_record = ResearchCoverage(
            run_id=run_id,
            evidence_class=evidence_class,
            status=cov_status.value if isinstance(cov_status, CoverageStatus) else cov_status,
        )
        session.add(cov_record)
    print(f"DEBUG SERVICE: Added {len(coverage)} coverage records", file=sys.stderr, flush=True)

    # Create claim records and evidence links
    claims = result.get("claims", [])
    print(f"DEBUG SERVICE: Processing {len(claims)} claims from workflow", file=sys.stderr, flush=True)
    for claim_output in claims:
        # Map claim type enum value
        claim_type_str = claim_output.claim_type.value if hasattr(claim_output.claim_type, "value") else str(claim_output.claim_type)

        # Use SUPPORTED status for all claims
        claim_status = ClaimStatus.SUPPORTED

        claim = Claim(
            case_id=case_id,
            statement=claim_output.statement,
            claim_type=claim_type_str,
            status=claim_status.value,
            generated_by=run_id,
            protocol_version=protocol.version,
            run_id=run_id,
        )
        session.add(claim)
        session.flush()

        # Create evidence links
        for evidence_id in claim_output.evidence_ids:
            evidence_link = ClaimEvidence(
                claim_id=claim.id,
                evidence_artifact_id=evidence_id,
            )
            session.add(evidence_link)
            session.flush()

            # Create dependency: EvidenceArtifact -> Claim
            add_dependency(
                session,
                upstream_kind="EvidenceArtifact",
                upstream_id=evidence_id,
                downstream_kind="Claim",
                downstream_id=claim.id,
            )

    # Transition case state to EVIDENCE_READY if ready, otherwise stay RESEARCHING
    if readiness.get("ready"):
        new_state = ResearchState.EVIDENCE_READY
        if can_transition(ResearchState(case.research_state), new_state):
            case.research_state = new_state.value

    # Commit all changes
    session.commit()
    print(f"DEBUG SERVICE: Committed all changes for run {run_id}", file=sys.stderr, flush=True)

    return run_id


def _create_run_id() -> str:
    """Generate a unique run ID."""
    import uuid
    return str(uuid.uuid4())


def _compute_prompt_hash() -> str:
    """Compute hash of all nine node prompts."""
    import hashlib
    from pathlib import Path

    prompt_dir = Path(__file__).parent / "prompts"
    node_names = [
        "01_resolve_identity",
        "02_current_context_formal_route",
        "03_recent_research_spine",
        "04_supervised_projects",
        "05_concept_method_corpus_genealogy",
        "06_project_funding_context",
        "07_route_translation",
        "08_contradictions_unknowns",
        "09_structured_synthesis",
    ]

    combined = ""
    for node_name in node_names:
        prompt_path = prompt_dir / f"{node_name}.md"
        if prompt_path.exists():
            combined += prompt_path.read_text()

    return hashlib.sha256(combined.encode()).hexdigest()
