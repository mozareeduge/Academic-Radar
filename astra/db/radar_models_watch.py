"""SQLAlchemy models for Radar watch, change events, and application briefs.

Implements OBJ-011 (WatchTarget), change events, OBJ-013 (ApplicationBrief),
and brief dependencies.
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
    Boolean,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.models import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# OBJ-011: WatchTarget
# ---------------------------------------------------------------------------
class WatchTarget(Base):
    __tablename__ = "radar_watch_targets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    url: Mapped[str] = mapped_column(String(2048))
    cadence: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("state IN ('ACTIVE', 'PAUSED', 'ERROR', 'RETIRED')"),
        default="ACTIVE",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_watch_targets_state", "state"),
    )


# ---------------------------------------------------------------------------
# Watch Checks
# ---------------------------------------------------------------------------
class WatchCheck(Base):
    __tablename__ = "radar_watch_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    watch_target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_watch_targets.id"), index=True
    )
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_source_snapshots.id"), index=True
    )
    changed: Mapped[bool] = mapped_column(Boolean, default=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_watch_checks_watch_target_at", "watch_target_id", "at"),
    )


# ---------------------------------------------------------------------------
# Change Events
# ---------------------------------------------------------------------------
class ChangeEvent(Base):
    __tablename__ = "radar_change_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    watch_check_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_watch_checks.id"), index=True
    )
    summary: Mapped[str] = mapped_column(Text)
    material: Mapped[bool] = mapped_column(Boolean, default=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_change_events_material_at", "material", "at"),
    )


# ---------------------------------------------------------------------------
# OBJ-013: ApplicationBrief
# ---------------------------------------------------------------------------
class ApplicationBrief(Base):
    __tablename__ = "radar_application_briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    frozen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("state IN ('DRAFT', 'REVIEWED', 'SUPERSEDED')"),
        default="DRAFT",
    )
    superseded_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("radar_application_briefs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_application_briefs_case_state", "case_id", "state"),
    )


# ---------------------------------------------------------------------------
# Brief Dependencies
# ---------------------------------------------------------------------------
class BriefDependency(Base):
    __tablename__ = "radar_brief_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    brief_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_application_briefs.id"), index=True
    )
    dependency_kind: Mapped[str] = mapped_column(String(64))
    dependency_id: Mapped[str] = mapped_column(String(36), index=True)
    dependency_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_brief_dependencies_brief_kind", "brief_id", "dependency_kind"),
    )
