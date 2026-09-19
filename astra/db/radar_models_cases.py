"""SQLAlchemy models for Radar evaluation cases and history.

Implements OBJ-004 (EvaluationCase) and supporting history/notes tables.
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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.models import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# OBJ-004: EvaluationCase
# ---------------------------------------------------------------------------
class EvaluationCase(Base):
    __tablename__ = "radar_evaluation_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_mozare_routes.id"), index=True
    )
    target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    application_route: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "application_route IN ('SUPERVISOR_FIRST_PHD', 'ADVERTISED_PHD', 'STRUCTURED_PHD', 'MA_PROGRAMME')"
        ),
    )
    research_state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "research_state IN ('DISCOVERED', 'TRIAGED', 'RESEARCHING', 'EVIDENCE_READY', 'STALE', 'FAILED', 'ARCHIVED')"
        ),
    )
    user_disposition: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("user_disposition IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')"),
        default="UNDECIDED",
    )
    suggested_disposition: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint("suggested_disposition IS NULL OR suggested_disposition IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')"),
    )
    application_stage: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "application_stage IN ('NOT_STARTED', 'PREPARING', 'CONTACTED', 'APPLICATION_OPEN', 'APPLIED', 'INTERVIEW', 'OFFER', 'DECLINED', 'CLOSED')"
        ),
        default="NOT_STARTED",
    )
    next_action: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint(
            "route_id", "target_id", "application_route",
            name="uq_radar_evaluation_cases_identity"
        ),
    )


# ---------------------------------------------------------------------------
# Case Disposition History
# ---------------------------------------------------------------------------
class CaseDispositionHistory(Base):
    __tablename__ = "radar_case_disposition_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    previous: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint("previous IS NULL OR previous IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')"),
    )
    new: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("new IN ('UNDECIDED', 'STRONG', 'WATCH', 'ACT', 'REJECTED')"),
    )
    actor: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("actor IN ('USER', 'SYSTEM_SUGGESTION')"),
    )
    reason: Mapped[Optional[str]] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------------------
# Application Stage History
# ---------------------------------------------------------------------------
class ApplicationStageHistory(Base):
    __tablename__ = "radar_application_stage_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    previous: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint(
            "previous IS NULL OR previous IN ('NOT_STARTED', 'PREPARING', 'CONTACTED', 'APPLICATION_OPEN', 'APPLIED', 'INTERVIEW', 'OFFER', 'DECLINED', 'CLOSED')"
        ),
    )
    new: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "new IN ('NOT_STARTED', 'PREPARING', 'CONTACTED', 'APPLICATION_OPEN', 'APPLIED', 'INTERVIEW', 'OFFER', 'DECLINED', 'CLOSED')"
        ),
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ---------------------------------------------------------------------------
# User Notes
# ---------------------------------------------------------------------------
class UserNotes(Base):
    __tablename__ = "radar_user_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
