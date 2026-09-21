"""Application brief freeze and supersession logic.

OBJ-013: ApplicationBrief — frozen, source-linked preparation artifact generated
from one case. Freezes current claims/gates/dimensions/funding with dependency
versions and snapshots. Refuses if any critical fact is STALE or any hard gate is
UNKNOWN.

DEC-022: The product prepares an evidence-backed brief but does not automatically
draft/send final correspondence as part of V1 product completion.

ORACLE-032: Application brief is candidate-bound and evidence-bound. Brief freezes
case/evidence version, identifies unknowns/prohibited claims, and becomes superseded
when dependent case evidence materially changes.

FLOW-009: Application preparation: ACT disposition -> ApplicationBrief -> verify
current deadlines/rules -> freeze brief -> downstream writing/outreach. No auto-send.

Implementation:
  - freeze_brief(session, case_id, protocol=None) -> str (brief_id)
    Builds content JSON from current claims/gates/dimensions/funding of the case
    where EVERY statement carries evidence ids and source freshness. Refuses (raises
    BriefBlocked with list) if any critical fact is STALE or any hard gate is
    UNKNOWN. Writes radar_application_briefs + radar_brief_dependencies rows.

  - is_superseded(session, brief_id) -> bool
    True when any recorded dependency's snapshot fingerprint changed. The old brief
    content is untouched.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import (
    Claim,
    GateAssessment,
    DimensionAssessment,
    FundingAssessment,
    ClaimEvidence,
)
from db.radar_models_evidence import (
    EvidenceArtifact,
    SourceSnapshot,
)
from db.radar_models_watch import ApplicationBrief, BriefDependency
from academic_radar.domain.enums import GateResult, ClaimStatus, ResearchState
from academic_radar.domain.protocols import Protocol
from academic_radar.research.protocol_loader import load_protocols
from academic_radar.domain.freshness import is_stale
from academic_radar.domain.case_truth import case_truth


class BriefBlocked(Exception):
    """Exception raised when brief cannot be frozen due to stale or unknown critical facts."""

    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


@dataclass
class DependencyRecord:
    """A recorded dependency of a brief on an external fact."""

    dependency_kind: str
    dependency_id: str
    dependency_version: Optional[str]


def _get_case_and_protocol(
    session: Session, case_id: str, protocol: Optional[Protocol] = None
) -> tuple[EvaluationCase, Protocol]:
    """Fetch case and load protocol by application_route."""
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).one_or_none()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    if protocol is None:
        protocols = load_protocols()
        route_key = case.application_route
        if route_key not in protocols:
            raise ValueError(f"No protocol found for route {route_key}")
        protocol = protocols[route_key]

    return case, protocol


def _check_stale_critical_facts(
    session: Session,
    case: EvaluationCase,
    protocol: Protocol,
    now: datetime,
) -> list[str]:
    """Check for stale critical facts. Return list of reasons if any found."""
    reasons = []

    for evidence_class in protocol.mandatory:
        freshness_threshold = protocol.freshness_days.get(evidence_class)
        if freshness_threshold is None:
            continue

        cutoff_time = now - timedelta(days=freshness_threshold)

        case_claims = session.query(Claim).filter(Claim.case_id == case.id).all()
        for claim in case_claims:
            evidence_links = session.query(ClaimEvidence).filter(
                ClaimEvidence.claim_id == claim.id
            ).all()

            for ce in evidence_links:
                artifact = session.query(EvidenceArtifact).filter(
                    EvidenceArtifact.id == ce.evidence_artifact_id
                ).one_or_none()

                if artifact and artifact.retrieved_at:
                    retrieved = artifact.retrieved_at
                    if retrieved.tzinfo is None:
                        retrieved = retrieved.replace(tzinfo=timezone.utc)
                    if retrieved < cutoff_time:
                        reasons.append(
                            f"Evidence retrieved {(now - retrieved).days} days ago "
                            f"exceeds threshold of {freshness_threshold} days"
                        )
                        return reasons

    return reasons


def _check_unknown_hard_gates(
    session: Session, case: EvaluationCase
) -> list[str]:
    """Check for hard gates with UNKNOWN result. Return list of reasons if any found."""
    reasons = []

    hard_unknown_gates = session.query(GateAssessment).filter(
        and_(
            GateAssessment.case_id == case.id,
            GateAssessment.result == GateResult.UNKNOWN.value,
        )
    ).all()

    for gate in hard_unknown_gates:
        reasons.append(f"Hard gate unknown: {gate.requirement}")

    return reasons


def _collect_brief_content(
    session: Session, case: EvaluationCase
) -> dict:
    """Collect all current claims, gates, dimensions, and funding for the brief."""
    content = {
        "case_id": case.id,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "claims": [],
        "gates": [],
        "dimensions": [],
        "funding_assessments": [],
    }

    claims = session.query(Claim).filter(Claim.case_id == case.id).all()
    for claim in claims:
        evidence_ids = []
        evidence_artifacts = session.query(ClaimEvidence).filter(
            ClaimEvidence.claim_id == claim.id
        ).all()
        for ce in evidence_artifacts:
            artifact = session.query(EvidenceArtifact).filter(
                EvidenceArtifact.id == ce.evidence_artifact_id
            ).one()
            evidence_ids.append({
                "id": artifact.id,
                "source_url": artifact.source_url,
                "retrieved_at": artifact.retrieved_at.isoformat() if artifact.retrieved_at else None,
            })

        content["claims"].append({
            "id": claim.id,
            "statement": claim.statement,
            "claim_type": claim.claim_type,
            "status": claim.status,
            "evidence_ids": evidence_ids,
            "created_at": claim.created_at.isoformat(),
        })

    gates = session.query(GateAssessment).filter(GateAssessment.case_id == case.id).all()
    for gate in gates:
        content["gates"].append({
            "id": gate.id,
            "requirement": gate.requirement,
            "result": gate.result,
            "evidence_ids": gate.evidence_ids or [],
            "effective_date": gate.effective_date.isoformat() if gate.effective_date else None,
        })

    dimensions = session.query(DimensionAssessment).filter(
        DimensionAssessment.case_id == case.id
    ).all()
    for dim in dimensions:
        content["dimensions"].append({
            "id": dim.id,
            "dimension_id": dim.dimension_id,
            "scale": dim.scale,
            "value": dim.value,
            "unknowns": dim.unknowns,
        })

    funding_assessments = session.query(FundingAssessment).filter(
        FundingAssessment.case_id == case.id
    ).all()
    for funding in funding_assessments:
        content["funding_assessments"].append({
            "id": funding.id,
            "funding_route_id": funding.funding_route_id,
            "state": funding.state,
            "award_amount": str(funding.award_amount) if funding.award_amount else None,
            "tuition_amount": str(funding.tuition_amount) if funding.tuition_amount else None,
            "currency": funding.currency,
        })

    return content


def _record_dependencies(
    session: Session,
    brief_id: str,
    case: EvaluationCase,
) -> None:
    """Record dependencies from brief to all current evidence snapshots."""
    artifacts = session.query(EvidenceArtifact).join(
        ClaimEvidence,
        ClaimEvidence.evidence_artifact_id == EvidenceArtifact.id,
    ).join(
        Claim,
        ClaimEvidence.claim_id == Claim.id,
    ).filter(
        Claim.case_id == case.id,
    ).distinct().all()

    for artifact in artifacts:
        if artifact.snapshot_id:
            snapshot = session.query(SourceSnapshot).filter(
                SourceSnapshot.id == artifact.snapshot_id
            ).one()

            dep = BriefDependency(
                brief_id=brief_id,
                dependency_kind="SourceSnapshot",
                dependency_id=snapshot.id,
                dependency_version=snapshot.fingerprint,
            )
            session.add(dep)

    for gate in session.query(GateAssessment).filter(GateAssessment.case_id == case.id).all():
        if gate.evidence_ids:
            for evidence_id in gate.evidence_ids:
                dep = BriefDependency(
                    brief_id=brief_id,
                    dependency_kind="GateAssessment",
                    dependency_id=gate.id,
                    dependency_version=gate.result,
                )
                session.add(dep)
                break

    session.flush()


def freeze_brief(
    session: Session,
    case_id: str,
    protocol: Optional[Protocol] = None,
) -> str:
    """Freeze an application brief from the current case state.

    Builds content JSON from current claims/gates/dimensions/funding where EVERY
    statement carries evidence ids and source freshness. Refuses (raises BriefBlocked
    with list) if any critical fact is STALE or any hard gate is UNKNOWN.

    Args:
        session: Database session.
        case_id: ID of the evaluation case to freeze.
        protocol: Optional protocol; if None, loaded by case's application_route.

    Returns:
        ID of the created ApplicationBrief.

    Raises:
        BriefBlocked: If any critical fact is stale or hard gate is unknown.
        ValueError: If case not found.
    """
    case, protocol = _get_case_and_protocol(session, case_id, protocol)

    now = datetime.now(timezone.utc)

    blocked_reasons = case_truth(session, case, protocol, now=now).brief_block_reasons
    if blocked_reasons:
        raise BriefBlocked(blocked_reasons)

    content = _collect_brief_content(session, case)

    brief = ApplicationBrief(
        case_id=case_id,
        frozen_at=now,
        content=content,
        state="DRAFT",
    )
    session.add(brief)
    session.flush()

    _record_dependencies(session, brief.id, case)
    session.flush()

    return brief.id


def is_superseded(session: Session, brief_id: str) -> bool:
    """Check if a brief has been superseded by dependency changes.

    A brief is superseded when any recorded dependency's snapshot fingerprint has
    changed (or the snapshot is missing). The old brief content remains untouched.

    Args:
        session: Database session.
        brief_id: ID of the brief to check.

    Returns:
        True if any dependency has changed, False otherwise.
    """
    brief = session.query(ApplicationBrief).filter(ApplicationBrief.id == brief_id).one_or_none()
    if not brief:
        return False

    deps = session.query(BriefDependency).filter(BriefDependency.brief_id == brief_id).all()

    for dep in deps:
        if dep.dependency_kind == "SourceSnapshot":
            snapshot = session.query(SourceSnapshot).filter(
                SourceSnapshot.id == dep.dependency_id
            ).one_or_none()

            if not snapshot:
                return True

            if dep.dependency_version != snapshot.fingerprint:
                return True

    return False
