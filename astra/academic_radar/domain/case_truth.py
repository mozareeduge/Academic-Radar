"""Backend-owned case facts and application brief readiness.

Coverage rows do not identify the evidence class of claim artifacts. Do not
apply a protocol class's freshness threshold to an unrelated artifact.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import (
    Claim, ClaimEvidence, DimensionAssessment, FundingAssessment, GateAssessment,
)
from db.radar_models_targets import Programme, RadarOpportunity
from academic_radar.domain.protocols import Protocol


@dataclass(frozen=True)
class CaseTruth:
    blockers: list[dict]
    unknown_count: int
    deadline: dict | None
    freshness: bool | None
    brief_block_reasons: list[str]


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def case_truth(session: Session, case: EvaluationCase, protocol: Protocol, *, now: datetime | None = None) -> CaseTruth:
    now = now or datetime.now(timezone.utc)
    claims = session.query(Claim).filter(Claim.case_id == case.id).all()
    gates = session.query(GateAssessment).filter(GateAssessment.case_id == case.id).all()
    dimensions = session.query(DimensionAssessment).filter(DimensionAssessment.case_id == case.id).all()
    funding = session.query(FundingAssessment).filter(FundingAssessment.case_id == case.id).all()

    blockers = [
        {"name": gate.requirement, "status": "FAIL", "reason": "Formal gate failed"}
        for gate in gates if gate.result == "FAIL"
    ]
    blockers.extend(
        {"name": "Funding eligibility", "status": "FAIL", "reason": "Funding route formally blocked"}
        for item in funding if item.state == "FORMALLY_BLOCKED"
    )
    unknown_count = (
        sum(claim.status == "UNKNOWN" for claim in claims)
        + sum(gate.result == "UNKNOWN" for gate in gates)
        + sum(dim.value is None or bool(dim.unknowns) for dim in dimensions)
        + sum(item.state == "ELIGIBILITY_UNKNOWN" for item in funding)
    )

    target = None
    if case.application_route == "MA_PROGRAMME":
        target = session.query(Programme).filter(Programme.target_entity_id == case.target_id).first()
    elif case.application_route in ("ADVERTISED_PHD", "STRUCTURED_PHD"):
        target = session.query(RadarOpportunity).filter(RadarOpportunity.target_entity_id == case.target_id).first()
    deadline = None
    if target is not None and target.deadline_original_text:
        deadline = {
            "original_text": target.deadline_original_text,
            "precision": target.deadline_precision,
        }

    stale_reasons = []
    if case.research_state == "STALE":
        stale_reasons.append("Case research is stale")
    for gate in gates:
        if gate.result == "STALE":
            stale_reasons.append(f"Hard gate stale: {gate.requirement}")
    for claim in claims:
        if claim.status == "STALE":
            stale_reasons.append(f"Claim stale: {claim.statement}")
    if deadline:
        checked = target.deadline_last_checked_at
        threshold = protocol.freshness_days.get("DEADLINE")
        if checked is None:
            stale_reasons.append("Deadline has not been checked")
        elif threshold is not None and _utc(checked) < now - timedelta(days=threshold):
            stale_reasons.append("Deadline needs rechecking")

    # A nullable value preserves the distinction between fresh and not assessed.
    checked_facts = any(claim.last_checked_at for claim in claims) or bool(
        deadline and target.deadline_last_checked_at
    )
    freshness = False if stale_reasons else (True if checked_facts else None)

    reasons = []
    if case.user_disposition != "ACT":
        reasons.append("Case disposition must be ACT")
    if case.research_state != "EVIDENCE_READY":
        reasons.append("Case research must be EVIDENCE_READY")
    reasons.extend(f"Hard gate failed: {gate.requirement}" for gate in gates if gate.result == "FAIL")
    reasons.extend(f"Hard gate unknown: {gate.requirement}" for gate in gates if gate.result == "UNKNOWN")
    reasons.extend(
        "Funding route formally blocked" for item in funding if item.state == "FORMALLY_BLOCKED"
    )
    reasons.extend(stale_reasons)
    for claim in claims:
        if claim.status == "SUPPORTED" and claim.claim_type in ("EXTERNAL_FACT", "OBSERVED_RELATION"):
            if not session.query(ClaimEvidence.id).filter(ClaimEvidence.claim_id == claim.id).first():
                reasons.append(f"Supported claim lacks evidence: {claim.statement}")
    # UNKNOWN claims and dimensions remain visible in the brief, as HZN-018 permits.
    return CaseTruth(blockers, unknown_count, deadline, freshness, list(dict.fromkeys(reasons)))
