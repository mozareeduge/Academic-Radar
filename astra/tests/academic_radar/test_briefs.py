"""Tests for application brief freeze and supersession logic.

ORACLE-032: Application brief is candidate-bound and evidence-bound. Brief freezes
case/evidence version, identifies unknowns/prohibited claims, and becomes superseded
when dependent case evidence materially changes.

QA-P14: Application brief freeze
Generate brief, capture dependency versions, change a critical source, verify old
brief becomes superseded; user can inspect changed facts and generate a new brief.
"""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from academic_radar.domain.briefs import (
    freeze_brief,
    is_superseded,
    BriefBlocked,
)
from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import Claim, GateAssessment, ClaimEvidence
from db.radar_models_evidence import EvidenceArtifact, SourceSnapshot
from db.radar_models_watch import ApplicationBrief, BriefDependency
from db.radar_models_targets import TargetEntity


def make_temp_db():
    """Create a temporary SQLite database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    normalized_path = path.replace("\\", "/")
    return f"sqlite:///{normalized_path}", path


@pytest.fixture
def db_session():
    """Fixture providing a database session with migrations applied."""
    db_url, path = make_temp_db()
    try:
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Alembic upgrade failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
        engine = create_engine(db_url)
        with Session(engine) as session:
            yield session
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def setup_case_with_evidence(db_session: Session):
    """Create test case with claims, gates, and evidence artifacts."""
    now = datetime.now(timezone.utc)

    route_id = "route-ma"
    case_id = "case-brief-test"
    prog_id = "target-prog"
    snapshot_id = "snap-1"
    artifact_id = "artifact-1"
    claim_id = "claim-1"
    gate_id = "gate-1"
    claim_evidence_id = "claim-evidence-1"

    db_session.execute(
        text("""
            INSERT INTO radar_mozare_routes (id, name, state, created_at, updated_at)
            VALUES (:id, :name, :state, :created_at, :updated_at)
        """),
        {
            "id": route_id,
            "name": "MA Programme",
            "state": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_target_entities (id, kind, display_name, created_at, updated_at)
            VALUES (:id, :kind, :display_name, :created_at, :updated_at)
        """),
        {
            "id": prog_id,
            "kind": "Programme",
            "display_name": "Test Programme",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_evaluation_cases
            (id, route_id, target_id, application_route, research_state, user_disposition,
             application_stage, created_at, updated_at)
            VALUES (:id, :route_id, :target_id, :application_route, :research_state,
                    :user_disposition, :application_stage, :created_at, :updated_at)
        """),
        {
            "id": case_id,
            "route_id": route_id,
            "target_id": prog_id,
            "application_route": "MA_PROGRAMME",
            "research_state": "EVIDENCE_READY",
            "user_disposition": "ACT",
            "application_stage": "APPLICATION_OPEN",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_source_snapshots
            (id, source_url, state, fingerprint, captured_at, created_at, updated_at)
            VALUES (:id, :source_url, :state, :fingerprint, :captured_at, :created_at, :updated_at)
        """),
        {
            "id": snapshot_id,
            "source_url": "https://example.com/programme",
            "state": "CAPTURED",
            "fingerprint": "hash-v1",
            "captured_at": now,
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_evidence_artifacts
            (id, source_url, source_type, snapshot_id, retrieved_at, source_authority, created_at, updated_at)
            VALUES (:id, :source_url, :source_type, :snapshot_id, :retrieved_at, :source_authority, :created_at, :updated_at)
        """),
        {
            "id": artifact_id,
            "source_url": "https://example.com/programme",
            "source_type": "OFFICIAL_PROGRAMME",
            "snapshot_id": snapshot_id,
            "retrieved_at": now,
            "source_authority": "OFFICIAL_PROGRAMME",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_claims
            (id, case_id, statement, claim_type, status, created_at, updated_at)
            VALUES (:id, :case_id, :statement, :claim_type, :status, :created_at, :updated_at)
        """),
        {
            "id": claim_id,
            "case_id": case_id,
            "statement": "Programme accepts international students",
            "claim_type": "EXTERNAL_FACT",
            "status": "SUPPORTED",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_claim_evidence
            (id, claim_id, evidence_artifact_id, created_at, updated_at)
            VALUES (:id, :claim_id, :evidence_artifact_id, :created_at, :updated_at)
        """),
        {
            "id": claim_evidence_id,
            "claim_id": claim_id,
            "evidence_artifact_id": artifact_id,
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_gate_assessments
            (id, case_id, requirement, source_authority, result, created_at, updated_at)
            VALUES (:id, :case_id, :requirement, :source_authority, :result, :created_at, :updated_at)
        """),
        {
            "id": gate_id,
            "case_id": case_id,
            "requirement": "English proficiency",
            "source_authority": "OFFICIAL_PROGRAMME",
            "result": "PASS",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.commit()

    return {
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "artifact_id": artifact_id,
        "claim_id": claim_id,
    }


def test_brief_lists_dependencies(db_session: Session, setup_case_with_evidence):
    """Brief contains dependency records for all evidence snapshots."""
    case_id = setup_case_with_evidence["case_id"]
    snapshot_id = setup_case_with_evidence["snapshot_id"]

    brief_id = freeze_brief(db_session, case_id)

    brief = db_session.query(ApplicationBrief).filter(ApplicationBrief.id == brief_id).one()
    assert brief.case_id == case_id
    assert brief.state == "DRAFT"
    assert brief.frozen_at is not None

    deps = db_session.query(BriefDependency).filter(
        BriefDependency.brief_id == brief_id
    ).all()
    assert len(deps) > 0
    assert any(d.dependency_id == snapshot_id for d in deps)


def test_brief_unchanged_snapshot_not_superseded(db_session: Session, setup_case_with_evidence):
    """Brief not superseded when snapshot fingerprint unchanged."""
    case_id = setup_case_with_evidence["case_id"]

    brief_id = freeze_brief(db_session, case_id)
    assert not is_superseded(db_session, brief_id)


def test_brief_changed_snapshot_marks_superseded(db_session: Session, setup_case_with_evidence):
    """Brief becomes superseded when snapshot fingerprint changes."""
    case_id = setup_case_with_evidence["case_id"]
    snapshot_id = setup_case_with_evidence["snapshot_id"]

    brief_id = freeze_brief(db_session, case_id)
    assert not is_superseded(db_session, brief_id)

    db_session.execute(
        text("UPDATE radar_source_snapshots SET fingerprint = :new_fp WHERE id = :id"),
        {"new_fp": "hash-v2-changed", "id": snapshot_id}
    )
    db_session.commit()

    assert is_superseded(db_session, brief_id)


def test_brief_old_content_untouched_after_supersession(db_session: Session, setup_case_with_evidence):
    """Old brief content remains untouched after supersession."""
    case_id = setup_case_with_evidence["case_id"]
    snapshot_id = setup_case_with_evidence["snapshot_id"]

    brief_id = freeze_brief(db_session, case_id)

    brief_before = db_session.query(ApplicationBrief).filter(
        ApplicationBrief.id == brief_id
    ).one()
    content_before = brief_before.content

    db_session.execute(
        text("UPDATE radar_source_snapshots SET fingerprint = :new_fp WHERE id = :id"),
        {"new_fp": "hash-v2-changed", "id": snapshot_id}
    )
    db_session.commit()

    brief_after = db_session.query(ApplicationBrief).filter(
        ApplicationBrief.id == brief_id
    ).one()

    assert brief_after.content == content_before
    assert is_superseded(db_session, brief_id)


def test_stale_evidence_blocks_freeze(db_session: Session):
    """Freeze blocked if evidence is stale beyond freshness threshold."""
    now = datetime.now(timezone.utc)
    stale_time = now - timedelta(days=31)

    route_id = "route-ma-stale"
    case_id = "case-stale-test"
    prog_id = "target-prog-stale"
    snapshot_id = "snap-stale"
    artifact_id = "artifact-stale"
    claim_id = "claim-stale"

    db_session.execute(
        text("""
            INSERT INTO radar_mozare_routes (id, name, state, created_at, updated_at)
            VALUES (:id, :name, :state, :created_at, :updated_at)
        """),
        {
            "id": route_id,
            "name": "MA Programme",
            "state": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_target_entities (id, kind, display_name, created_at, updated_at)
            VALUES (:id, :kind, :display_name, :created_at, :updated_at)
        """),
        {
            "id": prog_id,
            "kind": "Programme",
            "display_name": "Test Programme",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_evaluation_cases
            (id, route_id, target_id, application_route, research_state, user_disposition,
             application_stage, created_at, updated_at)
            VALUES (:id, :route_id, :target_id, :application_route, :research_state,
                    :user_disposition, :application_stage, :created_at, :updated_at)
        """),
        {
            "id": case_id,
            "route_id": route_id,
            "target_id": prog_id,
            "application_route": "MA_PROGRAMME",
            "research_state": "EVIDENCE_READY",
            "user_disposition": "ACT",
            "application_stage": "APPLICATION_OPEN",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_source_snapshots
            (id, source_url, state, fingerprint, captured_at, created_at, updated_at)
            VALUES (:id, :source_url, :state, :fingerprint, :captured_at, :created_at, :updated_at)
        """),
        {
            "id": snapshot_id,
            "source_url": "https://example.com/programme",
            "state": "CAPTURED",
            "fingerprint": "hash-v1",
            "captured_at": stale_time,
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_evidence_artifacts
            (id, source_url, source_type, snapshot_id, retrieved_at, source_authority, created_at, updated_at)
            VALUES (:id, :source_url, :source_type, :snapshot_id, :retrieved_at, :source_authority, :created_at, :updated_at)
        """),
        {
            "id": artifact_id,
            "source_url": "https://example.com/programme",
            "source_type": "OFFICIAL_PROGRAMME",
            "snapshot_id": snapshot_id,
            "retrieved_at": stale_time,
            "source_authority": "OFFICIAL_PROGRAMME",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_claims
            (id, case_id, statement, claim_type, status, created_at, updated_at)
            VALUES (:id, :case_id, :statement, :claim_type, :status, :created_at, :updated_at)
        """),
        {
            "id": claim_id,
            "case_id": case_id,
            "statement": "Programme accepts international students",
            "claim_type": "EXTERNAL_FACT",
            "status": "SUPPORTED",
            "created_at": now,
            "updated_at": now,
        }
    )

    claim_evidence_id = "claim-evidence-stale"
    db_session.execute(
        text("""
            INSERT INTO radar_claim_evidence
            (id, claim_id, evidence_artifact_id, created_at, updated_at)
            VALUES (:id, :claim_id, :evidence_artifact_id, :created_at, :updated_at)
        """),
        {
            "id": claim_evidence_id,
            "claim_id": claim_id,
            "evidence_artifact_id": artifact_id,
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.commit()

    with pytest.raises(BriefBlocked) as exc_info:
        freeze_brief(db_session, case_id)

    assert len(exc_info.value.reasons) > 0


def test_unknown_hard_gate_blocks_freeze(db_session: Session):
    """Freeze blocked if a hard gate is UNKNOWN."""
    now = datetime.now(timezone.utc)

    route_id = "route-unknown-gate"
    case_id = "case-unknown-gate"
    prog_id = "target-unknown-gate"
    gate_id = "gate-unknown"

    db_session.execute(
        text("""
            INSERT INTO radar_mozare_routes (id, name, state, created_at, updated_at)
            VALUES (:id, :name, :state, :created_at, :updated_at)
        """),
        {
            "id": route_id,
            "name": "MA Programme",
            "state": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_target_entities (id, kind, display_name, created_at, updated_at)
            VALUES (:id, :kind, :display_name, :created_at, :updated_at)
        """),
        {
            "id": prog_id,
            "kind": "Programme",
            "display_name": "Test Programme",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_evaluation_cases
            (id, route_id, target_id, application_route, research_state, user_disposition,
             application_stage, created_at, updated_at)
            VALUES (:id, :route_id, :target_id, :application_route, :research_state,
                    :user_disposition, :application_stage, :created_at, :updated_at)
        """),
        {
            "id": case_id,
            "route_id": route_id,
            "target_id": prog_id,
            "application_route": "MA_PROGRAMME",
            "research_state": "EVIDENCE_READY",
            "user_disposition": "ACT",
            "application_stage": "APPLICATION_OPEN",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.execute(
        text("""
            INSERT INTO radar_gate_assessments
            (id, case_id, requirement, source_authority, result, created_at, updated_at)
            VALUES (:id, :case_id, :requirement, :source_authority, :result, :created_at, :updated_at)
        """),
        {
            "id": gate_id,
            "case_id": case_id,
            "requirement": "English language requirement",
            "source_authority": "OFFICIAL_PROGRAMME",
            "result": "UNKNOWN",
            "created_at": now,
            "updated_at": now,
        }
    )

    db_session.commit()

    with pytest.raises(BriefBlocked) as exc_info:
        freeze_brief(db_session, case_id)

    assert len(exc_info.value.reasons) > 0
    assert "Hard gate unknown" in exc_info.value.reasons[0]


def test_no_networking_imports():
    """Module does not import smtplib, email, or requests."""
    import academic_radar.domain.briefs as briefs_module

    source_code = open(briefs_module.__file__).read()

    assert "import smtplib" not in source_code
    assert "import email" not in source_code
    assert "import requests" not in source_code
    assert "from smtplib" not in source_code
    assert "from email" not in source_code
    assert "from requests" not in source_code
