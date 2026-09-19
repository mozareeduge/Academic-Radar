"""SQLAlchemy models for Radar claims and assessments.

Implements OBJ-005 (Claim), OBJ-008 (SupervisionPrecedent), OBJ-009 (GateAssessment),
OBJ-010 (DimensionAssessment), and OBJ-015 (FundingAssessment).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.models import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# OBJ-005: Claim
# ---------------------------------------------------------------------------
class Claim(Base):
    __tablename__ = "radar_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    statement: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "claim_type IN ('EXTERNAL_FACT', 'OBSERVED_RELATION', 'INFERENCE', 'USER_DECISION')"
        ),
    )
    status: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "status IN ('SUPPORTED', 'PARTIAL', 'CONTRADICTED', 'UNKNOWN', 'STALE')"
        ),
    )
    generated_by: Mapped[Optional[str]] = mapped_column(String(128))
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("radar_research_runs.id"))
    protocol_version: Mapped[Optional[str]] = mapped_column(String(64))
    reviewed_by_user: Mapped[bool] = mapped_column(default=False)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Claim Evidence Link
# ---------------------------------------------------------------------------
class ClaimEvidence(Base):
    __tablename__ = "radar_claim_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_claims.id"), index=True
    )
    evidence_artifact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evidence_artifacts.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# OBJ-009: GateAssessment
# ---------------------------------------------------------------------------
class GateAssessment(Base):
    __tablename__ = "radar_gate_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    requirement: Mapped[str] = mapped_column(Text)
    source_authority: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "source_authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', 'OFFICIAL_DEPARTMENT_OR_PERSON', "
            "'AUTHORITATIVE_REGISTRY', 'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')"
        ),
    )
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    evaluation_rule: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "result IN ('PASS', 'FAIL', 'UNKNOWN', 'NOT_APPLICABLE', 'STALE')"
        ),
    )
    evidence_ids: Mapped[Optional[dict]] = mapped_column(JSON)
    provenance: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# OBJ-010: DimensionAssessment
# ---------------------------------------------------------------------------
class DimensionAssessment(Base):
    __tablename__ = "radar_dimension_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    dimension_id: Mapped[str] = mapped_column(String(64))
    scale: Mapped[str] = mapped_column(String(64))
    value: Mapped[Optional[int]] = mapped_column(
        Integer,
        CheckConstraint("value IS NULL OR (value >= 0 AND value <= 3)"),
    )
    unknowns: Mapped[Optional[dict]] = mapped_column(JSON)
    reviewer_status: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# OBJ-015: FundingAssessment
# ---------------------------------------------------------------------------
class FundingAssessment(Base):
    __tablename__ = "radar_funding_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    funding_route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    currency: Mapped[str] = mapped_column(String(3))
    award_amount: Mapped[Optional[Numeric]] = mapped_column(Numeric(14, 2))
    tuition_amount: Mapped[Optional[Numeric]] = mapped_column(Numeric(14, 2))
    duration_months: Mapped[Optional[int]] = mapped_column(Integer)
    known_costs: Mapped[Optional[dict]] = mapped_column(JSON)
    unknown_costs: Mapped[Optional[dict]] = mapped_column(JSON)
    uncovered_gap: Mapped[Optional[Numeric]] = mapped_column(Numeric(14, 2))
    state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "state IN ('ELIGIBLE', 'FUNDING_GAP', 'ELIGIBILITY_UNKNOWN', 'FORMALLY_BLOCKED')"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# OBJ-008: SupervisionPrecedent
# ---------------------------------------------------------------------------
class SupervisionPrecedent(Base):
    __tablename__ = "radar_supervision_precedents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    person_target_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id")
    )
    project_target_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id")
    )
    role: Mapped[str] = mapped_column(String(128))
    fields: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
