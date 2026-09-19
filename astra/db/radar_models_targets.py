"""SQLAlchemy models for Radar target entities, profiles, routes, and identities.

Implements OBJ-001 (CandidateProfile), OBJ-002 (MozareRoute), OBJ-003 (TargetEntity),
and supporting tables for identity resolution and entity relations.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# OBJ-001: CandidateProfile
# ---------------------------------------------------------------------------
class CandidateProfile(Base):
    __tablename__ = "radar_candidate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("state IN ('ACTIVE', 'NEEDS_VERIFICATION', 'SUPERSEDED')"),
        default="ACTIVE",
    )
    fixed_constraints: Mapped[Optional[str]] = mapped_column(Text)
    education: Mapped[Optional[str]] = mapped_column(JSON)
    language_evidence: Mapped[Optional[str]] = mapped_column(JSON)
    scholarly_work: Mapped[Optional[str]] = mapped_column(JSON)
    artistic_curatorial_work: Mapped[Optional[str]] = mapped_column(JSON)
    professional_technical_evidence: Mapped[Optional[str]] = mapped_column(JSON)
    verification_status: Mapped[Optional[str]] = mapped_column(Text)
    documents: Mapped[Optional[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CandidateEvidence(Base):
    __tablename__ = "radar_candidate_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_candidate_profiles.id"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(JSON)
    verified: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# OBJ-002: MozareRoute
# ---------------------------------------------------------------------------
class MozareRoute(Base):
    __tablename__ = "radar_mozare_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(256), index=True)
    state: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("state IN ('ACTIVE', 'EXPLORATORY', 'DORMANT', 'RETIRED')"),
        default="ACTIVE",
    )
    route_statement: Mapped[Optional[str]] = mapped_column(Text)
    core_problem: Mapped[Optional[str]] = mapped_column(Text)
    operations_methods: Mapped[Optional[str]] = mapped_column(JSON)
    relevant_corpora_material: Mapped[Optional[str]] = mapped_column(JSON)
    supporting_evidence: Mapped[Optional[str]] = mapped_column(JSON)
    target_disciplines: Mapped[Optional[str]] = mapped_column(JSON)
    prohibited_overclaims: Mapped[Optional[str]] = mapped_column(JSON)
    maturity: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# OBJ-003: TargetEntity
# ---------------------------------------------------------------------------
class TargetEntity(Base):
    __tablename__ = "radar_target_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    kind: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "kind IN ('Person', 'Programme', 'PhDOpportunity', 'FundedProject', 'Institution', 'FundingRoute', 'SupervisedProject', 'Work')"
        ),
    )
    display_name: Mapped[str] = mapped_column(String(512))
    canonical_url: Mapped[Optional[str]] = mapped_column(Text, index=True)
    doi: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    orcid: Mapped[Optional[str]] = mapped_column(String(64), index=True, unique=True)
    openalex_id: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    openaire_id: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    ror: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    attributes: Mapped[Optional[str]] = mapped_column(JSON)
    source_authority: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint(
            "source_authority IN ('OFFICIAL_REGULATION', 'OFFICIAL_PROGRAMME', 'OFFICIAL_DEPARTMENT_OR_PERSON', 'AUTHORITATIVE_REGISTRY', 'PRIMARY_RESEARCH_OUTPUT', 'REPUTABLE_SECONDARY', 'DISCOVERY_AGGREGATOR', 'UNKNOWN')"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_target_entities_kind", "kind"),
        Index("ix_radar_target_entities_display_name", "display_name"),
    )


# ---------------------------------------------------------------------------
# PersonIdentity (relates Person to Institution)
# ---------------------------------------------------------------------------
class PersonIdentity(Base):
    __tablename__ = "radar_person_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    identity_status: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint("identity_status IN ('RESOLVED', 'UNRESOLVED', 'CANDIDATE')"),
    )
    resolution_basis: Mapped[Optional[str]] = mapped_column(Text)
    candidate_set: Mapped[Optional[str]] = mapped_column(JSON)
    institution_target_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Programmes, Opportunities, Funding Routes (OBJ-003 types)
# ---------------------------------------------------------------------------
class Programme(Base):
    __tablename__ = "radar_programmes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(512))
    level: Mapped[Optional[str]] = mapped_column(String(64))
    duration_months: Mapped[Optional[int]] = mapped_column(Integer)
    languages: Mapped[Optional[str]] = mapped_column(JSON)
    admission_gates: Mapped[Optional[str]] = mapped_column(JSON)
    contact_details: Mapped[Optional[str]] = mapped_column(JSON)
    deadline_original_text: Mapped[Optional[str]] = mapped_column(Text)
    deadline_date: Mapped[Optional[date]] = mapped_column(Date)
    deadline_local_time: Mapped[Optional[time]] = mapped_column(Time)
    deadline_timezone: Mapped[Optional[str]] = mapped_column(String(64))
    deadline_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_precision: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint("deadline_precision IN ('DATE_ONLY', 'LOCAL_TIME', 'OFFSET_AWARE', 'AMBIGUOUS')"),
    )
    deadline_evidence_id: Mapped[Optional[str]] = mapped_column(String(36))
    deadline_last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Opportunity(Base):
    __tablename__ = "radar_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(512))
    application_route: Mapped[str] = mapped_column(
        String(32),
        CheckConstraint(
            "application_route IN ('SUPERVISOR_FIRST_PHD', 'ADVERTISED_PHD', 'STRUCTURED_PHD', 'MA_PROGRAMME')"
        ),
    )
    project_description: Mapped[Optional[str]] = mapped_column(Text)
    supervisor_info: Mapped[Optional[str]] = mapped_column(JSON)
    funding_status: Mapped[Optional[str]] = mapped_column(String(64))
    estimated_stipend: Mapped[Optional[str]] = mapped_column(String(64))
    deadline_original_text: Mapped[Optional[str]] = mapped_column(Text)
    deadline_date: Mapped[Optional[date]] = mapped_column(Date)
    deadline_local_time: Mapped[Optional[time]] = mapped_column(Time)
    deadline_timezone: Mapped[Optional[str]] = mapped_column(String(64))
    deadline_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_precision: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint("deadline_precision IN ('DATE_ONLY', 'LOCAL_TIME', 'OFFSET_AWARE', 'AMBIGUOUS')"),
    )
    deadline_evidence_id: Mapped[Optional[str]] = mapped_column(String(36))
    deadline_last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class FundingRoute(Base):
    __tablename__ = "radar_funding_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("radar_target_entities.id"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(512))
    funder: Mapped[Optional[str]] = mapped_column(String(256))
    award_amount: Mapped[Optional[str]] = mapped_column(String(64))
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    eligibility_criteria: Mapped[Optional[str]] = mapped_column(JSON)
    nomination_process: Mapped[Optional[str]] = mapped_column(Text)
    deadline_original_text: Mapped[Optional[str]] = mapped_column(Text)
    deadline_date: Mapped[Optional[date]] = mapped_column(Date)
    deadline_local_time: Mapped[Optional[time]] = mapped_column(Time)
    deadline_timezone: Mapped[Optional[str]] = mapped_column(String(64))
    deadline_utc: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deadline_precision: Mapped[Optional[str]] = mapped_column(
        String(32),
        CheckConstraint("deadline_precision IN ('DATE_ONLY', 'LOCAL_TIME', 'OFFSET_AWARE', 'AMBIGUOUS')"),
    )
    deadline_evidence_id: Mapped[Optional[str]] = mapped_column(String(36))
    deadline_last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Entity Relations (subject -> predicate -> object)
# ---------------------------------------------------------------------------
class EntityRelation(Base):
    __tablename__ = "radar_entity_relations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey("radar_target_entities.id"), index=True)
    predicate: Mapped[str] = mapped_column(String(256), index=True)
    object_id: Mapped[str] = mapped_column(String(36), ForeignKey("radar_target_entities.id"), index=True)
    evidence_ids: Mapped[Optional[str]] = mapped_column(JSON)
    identity_resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_radar_entity_relations_subject_predicate", "subject_id", "predicate"),
    )
