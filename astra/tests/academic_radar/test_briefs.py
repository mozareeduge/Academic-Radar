"""Test application brief freeze and supersession tracking.

Implements:
- OBJ-013: ApplicationBrief frozen, source-linked preparation artifact
- SCN-036/037: Generate brief, mark as superseded when case changes
- ORACLE-032: Brief freezes case/evidence version, becomes superseded when dependent case evidence materially changes
- DEC-022: Product prepares an evidence-backed brief but does not send correspondence
"""

import os
import subprocess
import sys
import tempfile

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from academic_radar.domain.briefs import freeze_brief, is_superseded, BriefBlockedError
from db.radar_models_watch import ApplicationBrief, BriefDependency
from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import Claim, GateAssessment
from db.radar_models_evidence import SourceSnapshot, EvidenceArtifact


def utcnow():
    return datetime.now(timezone.utc)


def make_temp_db():
    """Create a temporary SQLite database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    normalized_path = path.replace("\\", "/")
    return f"sqlite:///{normalized_path}", path


@pytest.fixture
def session():
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
        with Session(engine) as s:
            yield s
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def case_with_gates_and_claims(session):
    """Create a case with gates, claims, and evidence."""
    from sqlalchemy import text

    now = utcnow()

    session.execute(text("""
        INSERT INTO radar_mozare_routes
        (id, name, state, created_at, updated_at)
        VALUES ('route-001', 'Test Route', 'ACTIVE', :now, :now)
    """), {"now": now})

    session.execute(text("""
        INSERT INTO radar_target_entities
        (id, kind, display_name, created_at, updated_at)
        VALUES ('target-001', 'Person', 'Test Person', :now, :now)
    """), {"now": now})

    session.execute(text("""
        INSERT INTO radar_evaluation_cases
        (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
        VALUES ('case-001', 'route-001', 'target-001', 'SUPERVISOR_FIRST_PHD', 'EVIDENCE_READY', 'ACT', 'PREPARING', :now, :now)
    """), {"now": now})
    session.commit()

    # Create source snapshots
    snapshot1 = SourceSnapshot(
        id="snapshot-001",
        source_url="https://example.com/supervisor",
        fingerprint="fp-v1-001",
        state="CAPTURED",
        captured_at=utcnow(),
    )
    snapshot2 = SourceSnapshot(
        id="snapshot-002",
        source_url="https://example.com/requirements",
        fingerprint="fp-v1-002",
        state="CAPTURED",
        captured_at=utcnow(),
    )
    session.add_all([snapshot1, snapshot2])
    session.flush()

    # Create evidence artifacts
    evidence1 = EvidenceArtifact(
        id="evidence-001",
        source_url="https://example.com/supervisor",
        source_type="official_profile",
        snapshot_id="snapshot-001",
        retrieved_at=utcnow(),
        source_authority="OFFICIAL_DEPARTMENT_OR_PERSON",
    )
    evidence2 = EvidenceArtifact(
        id="evidence-002",
        source_url="https://example.com/requirements",
        source_type="programme_rules",
        snapshot_id="snapshot-002",
        retrieved_at=utcnow(),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add_all([evidence1, evidence2])
    session.flush()

    # Create claims
    claim1 = Claim(
        id="claim-001",
        case_id="case-001",
        statement="Supervisor is active researcher",
        claim_type="EXTERNAL_FACT",
        status="SUPPORTED",
        created_at=utcnow(),
    )
    claim2 = Claim(
        id="claim-002",
        case_id="case-001",
        statement="English language requirement",
        claim_type="EXTERNAL_FACT",
        status="SUPPORTED",
        created_at=utcnow(),
    )
    session.add_all([claim1, claim2])
    session.flush()

    # Create gates
    gate1 = GateAssessment(
        id="gate-001",
        case_id="case-001",
        requirement="Supervisor must be active",
        source_authority="OFFICIAL_DEPARTMENT_OR_PERSON",
        result="PASS",
        evidence_ids=["evidence-001"],
    )
    gate2 = GateAssessment(
        id="gate-002",
        case_id="case-001",
        requirement="English language",
        source_authority="OFFICIAL_PROGRAMME",
        result="PASS",
        evidence_ids=["evidence-002"],
    )
    session.add_all([gate1, gate2])
    session.flush()

    return {
        "case": case,
        "snapshots": [snapshot1, snapshot2],
        "evidence": [evidence1, evidence2],
        "claims": [claim1, claim2],
        "gates": [gate1, gate2],
    }


class TestFreezeBrief:
    """Test freeze_brief function creates snapshot of case state with dependencies."""

    def test_freeze_brief_creates_brief_with_content(self, session, case_with_gates_and_claims):
        """freeze_brief creates a DRAFT brief with frozen content."""
        case_id = "case-001"

        brief = freeze_brief(session, case_id)

        assert brief is not None
        assert brief.case_id == case_id
        assert brief.state == "DRAFT"
        assert brief.frozen_at is not None
        assert brief.content is not None
        assert isinstance(brief.content, dict)

    def test_freeze_brief_includes_claims_with_evidence_ids(self, session, case_with_gates_and_claims):
        """Brief content includes every claim with its evidence IDs."""
        brief = freeze_brief(session, "case-001")

        content = brief.content
        assert "claims" in content
        assert len(content["claims"]) > 0

        for claim_entry in content["claims"]:
            assert "statement" in claim_entry
            assert "claim_type" in claim_entry
            assert "status" in claim_entry
            assert "evidence_ids" in claim_entry
            assert isinstance(claim_entry["evidence_ids"], list)

    def test_freeze_brief_includes_gates_with_evidence_ids(self, session, case_with_gates_and_claims):
        """Brief content includes every gate with its evidence IDs."""
        brief = freeze_brief(session, "case-001")

        content = brief.content
        assert "gates" in content
        assert len(content["gates"]) > 0

        for gate_entry in content["gates"]:
            assert "requirement" in gate_entry
            assert "result" in gate_entry
            assert "evidence_ids" in gate_entry
            assert isinstance(gate_entry["evidence_ids"], (list, type(None)))

    def test_freeze_brief_records_snapshot_dependencies(self, session, case_with_gates_and_claims):
        """freeze_brief records radar_brief_dependencies for each source snapshot."""
        brief = freeze_brief(session, "case-001")

        deps = session.query(BriefDependency).filter_by(brief_id=brief.id).all()

        assert len(deps) > 0
        for dep in deps:
            assert dep.dependency_kind == "SourceSnapshot"
            assert dep.dependency_id is not None
            assert dep.dependency_version is not None

    def test_freeze_brief_captures_fingerprints(self, session, case_with_gates_and_claims):
        """Brief dependencies store snapshot fingerprints as version."""
        brief = freeze_brief(session, "case-001")

        deps = session.query(BriefDependency).filter_by(brief_id=brief.id).all()

        for dep in deps:
            snapshot = session.query(SourceSnapshot).filter_by(id=dep.dependency_id).first()
            if snapshot and snapshot.fingerprint:
                assert dep.dependency_version == snapshot.fingerprint

    def test_freeze_brief_refuses_if_stale_fact(self, session, case_with_gates_and_claims):
        """freeze_brief raises BriefBlockedError if any critical fact is STALE."""
        case_id = "case-001"

        claim = session.query(Claim).filter_by(case_id=case_id).first()
        claim.status = "STALE"
        session.flush()

        with pytest.raises(BriefBlockedError) as exc_info:
            freeze_brief(session, case_id)

        assert "stale" in str(exc_info.value).lower()

    def test_freeze_brief_refuses_if_unknown_hard_gate(self, session, case_with_gates_and_claims):
        """freeze_brief raises BriefBlockedError if any hard gate is UNKNOWN."""
        case_id = "case-001"

        gate = session.query(GateAssessment).filter_by(case_id=case_id).first()
        gate.result = "UNKNOWN"
        session.flush()

        with pytest.raises(BriefBlockedError) as exc_info:
            freeze_brief(session, case_id)

        assert "unknown" in str(exc_info.value).lower()

    def test_freeze_brief_blocked_exception_lists_blockers(self, session, case_with_gates_and_claims):
        """BriefBlockedError exception includes list of blocking facts."""
        gate = session.query(GateAssessment).filter_by(case_id="case-001").first()
        gate.result = "UNKNOWN"
        session.flush()

        with pytest.raises(BriefBlockedError) as exc_info:
            freeze_brief(session, "case-001")

        assert exc_info.value.blocked.blocking_facts is not None
        assert isinstance(exc_info.value.blocked.blocking_facts, list)
        assert len(exc_info.value.blocked.blocking_facts) > 0


class TestIsSuperseded:
    """Test is_superseded detects when brief dependencies have changed."""

    def test_is_superseded_false_when_snapshot_unchanged(self, session, case_with_gates_and_claims):
        """is_superseded returns False when all snapshot fingerprints match."""
        brief = freeze_brief(session, "case-001")

        assert is_superseded(session, brief.id) is False

    def test_is_superseded_true_when_snapshot_changed(self, session, case_with_gates_and_claims):
        """is_superseded returns True when any recorded dependency fingerprint changed."""
        brief = freeze_brief(session, "case-001")

        # Change a snapshot's fingerprint
        snapshot = session.query(SourceSnapshot).filter_by(id="snapshot-001").first()
        snapshot.fingerprint = "fp-v2-001-changed"
        session.flush()

        assert is_superseded(session, brief.id) is True

    def test_is_superseded_detects_only_brief_dependencies(self, session, case_with_gates_and_claims):
        """is_superseded only checks snapshots recorded in this brief's dependencies."""
        brief1 = freeze_brief(session, "case-001")

        # Create another unrelated snapshot
        snapshot3 = SourceSnapshot(
            id="snapshot-003",
            source_url="https://example.com/other",
            fingerprint="fp-v1-003",
            state="CAPTURED",
            captured_at=utcnow(),
        )
        session.add(snapshot3)
        session.flush()

        # Change the unrelated snapshot
        snapshot3.fingerprint = "fp-v2-003"
        session.flush()

        # Brief should not be superseded
        assert is_superseded(session, brief1.id) is False

    def test_is_superseded_true_when_multiple_dependencies_changed(self, session, case_with_gates_and_claims):
        """is_superseded returns True if any of multiple dependencies changed."""
        brief = freeze_brief(session, "case-001")

        # Change multiple snapshots
        snapshot1 = session.query(SourceSnapshot).filter_by(id="snapshot-001").first()
        snapshot2 = session.query(SourceSnapshot).filter_by(id="snapshot-002").first()
        snapshot1.fingerprint = "fp-v2-001"
        snapshot2.fingerprint = "fp-v2-002"
        session.flush()

        assert is_superseded(session, brief.id) is True


class TestNoMailImports:
    """Verify the module does not import email/smtp libraries."""

    def test_no_smtplib_in_briefs_module(self):
        """briefs.py does not import smtplib."""
        import academic_radar.domain.briefs as briefs_module
        import sys

        # Check that smtplib is not in the module's imported names
        assert "smtplib" not in sys.modules or not hasattr(briefs_module, "smtplib")

        # Read source to verify no imports
        import inspect
        source = inspect.getsource(briefs_module)
        assert "smtplib" not in source
        assert "email.smtp" not in source

    def test_no_email_in_briefs_module(self):
        """briefs.py does not import email module."""
        import academic_radar.domain.briefs as briefs_module
        import inspect

        source = inspect.getsource(briefs_module)
        assert "import email" not in source
        assert "from email" not in source

    def test_no_requests_in_briefs_module(self):
        """briefs.py does not import requests."""
        import academic_radar.domain.briefs as briefs_module
        import inspect

        source = inspect.getsource(briefs_module)
        assert "import requests" not in source
        assert "from requests" not in source
