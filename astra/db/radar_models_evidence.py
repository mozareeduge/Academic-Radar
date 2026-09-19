"""SQLAlchemy models for Radar evidence, protocols, runs, snapshots, and dependencies.

Implements OBJ-006 (EvidenceArtifact), OBJ-007 (Snapshot), OBJ-012 (ResearchRun),
OBJ-014 (ResearchProtocol), OBJ-016 (EvidenceDependency), OBJ-017 (DiscoveryTrace),
and OBJ-018 (SourceAuthority).
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
# OBJ-014: ResearchProtocol
# ---------------------------------------------------------------------------
class ResearchProtocol(Base):
    __tablename__ = "radar_research_protocols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    application_route: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "application_route IN ('SUPERVISOR_FIRST_PHD', 'ADVERTISED_PHD', 'STRUCTURED_PHD', 'MA_PROGRAMME')"
        ),
    )
    protocol_version: Mapped[str] = mapped_column(String(64))
    definition: Mapped[Optional[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_research_protocols_application_route", "application_route"),
        {"sqlite_autoincrement": False},
    )


# Add unique constraint for (application_route, protocol_version)
from sqlalchemy import UniqueConstraint
ResearchProtocol.__table_args__ = (
    UniqueConstraint("application_route", "protocol_version", name="uq_radar_research_protocols_route_version"),
    Index("ix_radar_research_protocols_application_route", "application_route"),
)


# ---------------------------------------------------------------------------
# OBJ-012: ResearchRun
# ---------------------------------------------------------------------------
class ResearchRun(Base):
    __tablename__ = "radar_research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_evaluation_cases.id"), index=True
    )
    protocol_version: Mapped[str] = mapped_column(String(64))
    model_id: Mapped[Optional[str]] = mapped_column(String(128))
    provider_id: Mapped[Optional[str]] = mapped_column(String(128))
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(64))
    schema_version: Mapped[Optional[str]] = mapped_column(String(64))
    run_identity: Mapped[Optional[str]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'CANCELLING', 'COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED')"
        ),
        default="QUEUED",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_research_runs_case_id", "case_id"),
        Index("ix_radar_research_runs_status", "status"),
    )


# ---------------------------------------------------------------------------
# OBJ-014 (continued): ResearchCoverage
# ---------------------------------------------------------------------------
class ResearchCoverage(Base):
    __tablename__ = "radar_research_coverage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_research_runs.id"), index=True
    )
    evidence_class: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "status IN ('SEARCHED_FOUND', 'SEARCHED_NONE_FOUND', 'NOT_SEARCHED', 'BLOCKED')"
        ),
    )
    evidence_ids: Mapped[Optional[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_research_coverage_run_id", "run_id"),
        Index("ix_radar_research_coverage_evidence_class", "evidence_class"),
    )


# ---------------------------------------------------------------------------
# OBJ-006: EvidenceArtifact
# ---------------------------------------------------------------------------
class EvidenceArtifact(Base):
    __tablename__ = "radar_evidence_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[Optional[str]] = mapped_column(String(64))
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    structured_extraction: Mapped[Optional[str]] = mapped_column(JSON)
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("radar_source_snapshots.id"), index=True
    )
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_authority: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "source_authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', "
            "'OFFICIAL_DEPARTMENT_OR_PERSON', 'AUTHORITATIVE_REGISTRY', "
            "'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')"
        ),
        default="UNKNOWN",
    )
    canonical_origin: Mapped[Optional[str]] = mapped_column(String(512), index=True)
    identity_confidence: Mapped[Optional[float]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_evidence_artifacts_source_url", "source_url"),
        Index("ix_radar_evidence_artifacts_snapshot_id", "snapshot_id"),
        Index("ix_radar_evidence_artifacts_canonical_origin", "canonical_origin"),
    )


# ---------------------------------------------------------------------------
# OBJ-007: SourceSnapshot
# ---------------------------------------------------------------------------
class SourceSnapshot(Base):
    __tablename__ = "radar_source_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_url: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[Optional[str]] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "state IN ('CAPTURED', 'UNCHANGED', 'CHANGED', 'FETCH_FAILED')"
        ),
    )
    content_ref: Mapped[Optional[str]] = mapped_column(Text)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_source_snapshots_source_url", "source_url"),
        Index("ix_radar_source_snapshots_captured_at", "captured_at"),
    )


# ---------------------------------------------------------------------------
# OBJ-018: SourceAuthority (controlled classification)
# ---------------------------------------------------------------------------
class SourceAuthority(Base):
    __tablename__ = "radar_source_authorities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    host_pattern: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    authority: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', "
            "'OFFICIAL_DEPARTMENT_OR_PERSON', 'AUTHORITATIVE_REGISTRY', "
            "'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_source_authorities_host_pattern", "host_pattern"),
    )


# ---------------------------------------------------------------------------
# OBJ-017: DiscoveryTrace
# ---------------------------------------------------------------------------
class DiscoveryTrace(Base):
    __tablename__ = "radar_discovery_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(128))
    query: Mapped[Optional[str]] = mapped_column(Text)
    run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("radar_research_runs.id"), index=True
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_discovery_traces_target_id", "target_id"),
        Index("ix_radar_discovery_traces_run_id", "run_id"),
        Index("ix_radar_discovery_traces_at", "at"),
    )


# ---------------------------------------------------------------------------
# OBJ-016: EvidenceDependency
# ---------------------------------------------------------------------------
class EvidenceDependency(Base):
    __tablename__ = "radar_evidence_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    upstream_kind: Mapped[str] = mapped_column(String(64))
    upstream_id: Mapped[str] = mapped_column(String(36))
    downstream_kind: Mapped[str] = mapped_column(String(64))
    downstream_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_evidence_dependencies_upstream", "upstream_kind", "upstream_id"),
        Index("ix_radar_evidence_dependencies_downstream", "downstream_kind", "downstream_id"),
    )
