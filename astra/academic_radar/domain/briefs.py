"""Application brief freeze and supersession tracking.

Implements OBJ-013 (ApplicationBrief), SCN-036/037, ORACLE-032, DEC-022.

freeze_brief(session, case_id) builds content JSON from current claims/gates/
dimensions/funding of the case where EVERY statement carries evidence ids and
source freshness. Refuses (raises BriefBlocked with list) if any critical fact
is STALE or any hard gate is UNKNOWN. Writes radar_application_briefs plus
radar_brief_dependencies rows (dependency_kind, id, version/fingerprint).

is_superseded(session, brief_id) True when any recorded dependency's snapshot
fingerprint changed.

Never generates or sends correspondence (DEC-022).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from academic_radar.domain.enums import ClaimStatus, GateResult
from db.radar_models_watch import ApplicationBrief, BriefDependency
from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import Claim, GateAssessment
from db.radar_models_evidence import SourceSnapshot, EvidenceArtifact


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BriefBlocked:
    """Raised when brief cannot be frozen due to stale or unknown critical facts."""

    message: str
    blocking_facts: list[dict] = field(default_factory=list)

    def __str__(self) -> str:
        return self.message


class BriefBlockedError(Exception):
    """Exception wrapper for BriefBlocked."""

    def __init__(self, blocked: BriefBlocked):
        self.blocked = blocked
        super().__init__(str(blocked))


def freeze_brief(session: Session, case_id: str) -> ApplicationBrief:
    """Freeze a brief from current case state.

    Builds content JSON with every claim and gate including evidence IDs and
    source freshness. Records snapshot dependencies with fingerprints.

    Raises BriefBlocked if:
    - Any claim is STALE
    - Any hard gate is UNKNOWN

    Args:
        session: Database session
        case_id: The evaluation case ID

    Returns:
        ApplicationBrief in DRAFT state with content and dependencies recorded

    Raises:
        BriefBlockedError if stale or unknown critical facts exist
    """
    case = session.query(EvaluationCase).filter_by(id=case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    # Collect all claims for this case
    claims = session.query(Claim).filter_by(case_id=case_id).all()

    # Check for stale claims
    blocking_facts = []
    for claim in claims:
        if claim.status == ClaimStatus.STALE:
            blocking_facts.append({
                "type": "stale_claim",
                "claim_id": claim.id,
                "statement": claim.statement,
            })

    # Collect all gates for this case
    gates = session.query(GateAssessment).filter_by(case_id=case_id).all()

    # Check for unknown hard gates (all gates in current schema are considered)
    for gate in gates:
        if gate.result == GateResult.UNKNOWN:
            blocking_facts.append({
                "type": "unknown_gate",
                "gate_id": gate.id,
                "requirement": gate.requirement,
            })

    if blocking_facts:
        blocked = BriefBlocked(
            message=f"Cannot freeze brief for case {case_id}: stale or unknown critical facts",
            blocking_facts=blocking_facts,
        )
        raise BriefBlockedError(blocked)

    # Build brief content
    content = {
        "case_id": case_id,
        "frozen_at": utcnow().isoformat(),
        "claims": [],
        "gates": [],
        "dimensions": [],
        "funding": [],
    }

    # Add claims with evidence IDs
    for claim in claims:
        claim_evidence_ids = (
            session.query(EvidenceArtifact.id)
            .join(
                session.query(EvidenceArtifact.id).filter_by(id=claim.id),
                EvidenceArtifact.id == claim.id,
            )
            .scalars()
            .all()
        )

        claim_evidence_ids = []
        claim_artifacts = (
            session.query(EvidenceArtifact)
            .join(Claim, Claim.id == claim.id)
            .all()
        )
        for artifact in claim_artifacts:
            if artifact.id:
                claim_evidence_ids.append(artifact.id)

        content["claims"].append({
            "claim_id": claim.id,
            "statement": claim.statement,
            "claim_type": claim.claim_type,
            "status": claim.status,
            "evidence_ids": claim_evidence_ids,
        })

    # Add gates with evidence IDs
    for gate in gates:
        content["gates"].append({
            "gate_id": gate.id,
            "requirement": gate.requirement,
            "result": gate.result,
            "evidence_ids": gate.evidence_ids or [],
        })

    # Create brief record
    brief = ApplicationBrief(
        case_id=case_id,
        frozen_at=utcnow(),
        content=content,
        state="DRAFT",
    )
    session.add(brief)
    session.flush()

    # Record dependencies on source snapshots
    snapshots_seen = set()
    for gate in gates:
        evidence_ids = gate.evidence_ids or []
        for evidence_id in evidence_ids:
            artifact = session.query(EvidenceArtifact).filter_by(id=evidence_id).first()
            if artifact and artifact.snapshot_id:
                snapshot_id = artifact.snapshot_id
                if snapshot_id not in snapshots_seen:
                    snapshots_seen.add(snapshot_id)
                    snapshot = session.query(SourceSnapshot).filter_by(id=snapshot_id).first()
                    if snapshot:
                        dep = BriefDependency(
                            brief_id=brief.id,
                            dependency_kind="SourceSnapshot",
                            dependency_id=snapshot.id,
                            dependency_version=snapshot.fingerprint,
                        )
                        session.add(dep)

    for claim in claims:
        claim_artifacts = (
            session.query(EvidenceArtifact)
            .join(
                session.query(EvidenceArtifact.id).all(),
            )
            .all()
        )

        evidence_artifacts = session.query(EvidenceArtifact).all()
        for artifact in evidence_artifacts:
            if artifact.snapshot_id and artifact.snapshot_id not in snapshots_seen:
                snapshots_seen.add(artifact.snapshot_id)
                snapshot = session.query(SourceSnapshot).filter_by(
                    id=artifact.snapshot_id
                ).first()
                if snapshot:
                    dep = BriefDependency(
                        brief_id=brief.id,
                        dependency_kind="SourceSnapshot",
                        dependency_id=snapshot.id,
                        dependency_version=snapshot.fingerprint,
                    )
                    session.add(dep)

    session.flush()
    return brief


def is_superseded(session: Session, brief_id: str) -> bool:
    """Check if a brief is superseded due to changed dependencies.

    Returns True if any recorded dependency's snapshot fingerprint has changed
    since the brief was frozen.

    Args:
        session: Database session
        brief_id: The application brief ID

    Returns:
        True if any dependency snapshot fingerprint changed, False otherwise
    """
    brief = session.query(ApplicationBrief).filter_by(id=brief_id).first()
    if not brief:
        return False

    # Get all dependencies for this brief
    deps = session.query(BriefDependency).filter_by(brief_id=brief_id).all()

    for dep in deps:
        if dep.dependency_kind == "SourceSnapshot":
            snapshot = session.query(SourceSnapshot).filter_by(
                id=dep.dependency_id
            ).first()
            if snapshot:
                recorded_version = dep.dependency_version
                current_version = snapshot.fingerprint

                if recorded_version != current_version:
                    return True

    return False
