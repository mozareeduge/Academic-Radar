"""Fixture mode evidence and provider setup.

Only used when RADAR_FIXTURE_MODE == '1'.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Tuple
from sqlalchemy.orm import Session

from academic_radar.evidence.snapshots import record_snapshot
from academic_radar.evidence.artifacts import create_artifact
from academic_radar.domain.enums import SnapshotState, SourceAuthority
from academic_radar.research.provider import MockProvider
from db.radar_models_cases import EvaluationCase

log = logging.getLogger(__name__)


def fixture_evidence_and_provider(
    session: Session,
    case: EvaluationCase,
) -> Tuple[MockProvider, dict]:
    """Create fixture evidence and return a MockProvider scripted to use it.

    Creates, for each mandatory class of the case's protocol:
    - One snapshot with fictional URL https://fixtures.example.org/<case_id>/<class>
    - One evidence artifact from that snapshot
    - Mock provider that returns VALID NodeOutput JSON citing those artifact IDs

    Args:
        session: SQLAlchemy session
        case: The EvaluationCase

    Returns:
        (MockProvider scripted with fixture responses, evidence_lookup dict)
    """
    log.info(f"fixture_evidence_and_provider called for case {case.id}")
    from academic_radar.research.protocol_loader import load_protocols

    # Load protocol
    protocols = load_protocols()
    protocol_key = case.application_route
    if protocol_key not in protocols:
        raise ValueError(f"Protocol {protocol_key} not found")
    protocol = protocols[protocol_key]
    log.info(f"Loaded protocol {protocol_key} with {len(protocol.mandatory)} mandatory classes")

    # Create fixtures for each mandatory class
    evidence_lookup = {}
    evidence_by_class = {}

    for mandatory_class in protocol.mandatory:
        # Create snapshot (uses raw SQL)
        fixture_url = f"https://fixtures.example.org/{case.id}/{mandatory_class}"
        snapshot = record_snapshot(
            session,
            url=fixture_url,
            text_or_none=f"Fixture content for {mandatory_class}",
            fetched_ok=True,
        )

        # Create artifact (uses raw SQL)
        artifact = create_artifact(
            session,
            snapshot=snapshot,
            source_url=fixture_url,
            source_type="text/plain",
            excerpt=f"Fixture excerpt for {mandatory_class}",
            published_at=datetime.now(timezone.utc),
        )

        evidence_lookup[artifact.id] = {
            "url": fixture_url,
            "class": mandatory_class,
        }
        evidence_by_class[mandatory_class] = artifact.id

    session.commit()

    # Create mock provider that returns valid NodeOutput for each node
    script = _build_fixture_script(protocol, evidence_by_class)
    provider = MockProvider(script)

    print(f"DEBUG FIXTURE: Created fixture provider with {len(evidence_by_class)} evidence artifacts", file=sys.stderr, flush=True)
    print(f"DEBUG FIXTURE: Script nodes: {list(script.keys())}", file=sys.stderr, flush=True)
    if script:
        first_key = list(script.keys())[0]
        first_output = json.loads(script[first_key])
        print(f"DEBUG FIXTURE: First node {first_key} has {len(first_output.get('claims', []))} claims", file=sys.stderr, flush=True)
    return provider, evidence_lookup


def _build_fixture_script(protocol, evidence_by_class: dict) -> dict:
    """Build script dict for MockProvider with fixture node outputs."""
    from academic_radar.domain.enums import CoverageStatus

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

    script = {}

    # Build coverage for ALL mandatory classes
    all_coverage = {}
    for mandatory_class in protocol.mandatory:
        all_coverage[mandatory_class] = "SEARCHED_FOUND"

    # Each node outputs ALL claims and coverage (simpler for fixture)
    # The first node outputs all mandatory claims
    for i, node_name in enumerate(node_names):
        claims = []
        coverage = dict(all_coverage)  # Copy all coverage to every node

        # Only the first node produces claims
        if i == 0:
            for mandatory_class in protocol.mandatory:
                if mandatory_class in evidence_by_class:
                    evidence_id = evidence_by_class[mandatory_class]
                    claims.append({
                        "statement": f"Fixture claim for {mandatory_class}",
                        "claim_type": "EXTERNAL_FACT",
                        "evidence_ids": [evidence_id],
                        "protocol_class": mandatory_class,
                        "unknowns": [],
                        "contradictions": [],
                    })


        output = {
            "schema_version": "1.0.0",
            "node": node_name,
            "claims": claims,
            "coverage": coverage,
        }
        script[node_name] = json.dumps(output)

    return script
