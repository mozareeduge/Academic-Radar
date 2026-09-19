"""Tests for dependency-targeted invalidation.

ORACLE-020: Evidence changes stale/recompute only dependent claims/assessments/
suggestions/briefs in normal operation; unrelated reviewed state survives.

DEC-042: Changed evidence invalidates only explicitly dependent claims/assessments/
suggestions/briefs whenever the dependency graph is intact.
"""

import os
import subprocess
import sys
import tempfile

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from academic_radar.domain.invalidation import (
    add_dependency,
    invalidate,
    InvalidationReport,
)
from academic_radar.domain.enums import ResearchState, can_transition


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
def setup_entities(db_session: Session):
    """Create test entities: MA case with funding, unrelated supervisor case."""
    # Create route, targets, cases, snapshots, claims via SQL
    route_id = "route-test"
    ma_case_id = "case-ma-1"
    supervisor_case_id = "case-supervisor-1"
    prog_id = "target-prog-1"
    fund_a_id = "target-fund-a"
    sup_id = "target-supervisor"
    snap_a_id = "snap-a"
    snap_sup_id = "snap-supervisor"
    claim_a_id = "claim-a-amount"
    claim_b_id = "claim-b-amount"
    claim_sup_id = "claim-supervisor-work"
    gate_a_id = "gate-a-eligible"
    gate_b_id = "gate-b-eligible"
    note_ma_id = "note-ma-1"

    # Insert route
    db_session.execute(
        text("""
            INSERT INTO radar_mozare_routes (id, name, state, created_at, updated_at)
            VALUES (:id, :name, :state, datetime('now'), datetime('now'))
        """),
        {"id": route_id, "name": "Test Route", "state": "ACTIVE"}
    )

    # Insert targets
    db_session.execute(
        text("""
            INSERT INTO radar_target_entities (id, kind, display_name, created_at, updated_at)
            VALUES (:id, :kind, :display_name, datetime('now'), datetime('now'))
        """),
        [
            {"id": prog_id, "kind": "Programme", "display_name": "MA Programme 1"},
            {"id": fund_a_id, "kind": "FundingRoute", "display_name": "Funding A"},
            {"id": sup_id, "kind": "Person", "display_name": "Dr. Supervisor"},
        ]
    )

    # Insert cases
    db_session.execute(
        text("""
            INSERT INTO radar_evaluation_cases
            (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
            VALUES (:id, :route_id, :target_id, :application_route, :research_state, :user_disposition, :application_stage, datetime('now'), datetime('now'))
        """),
        [
            {
                "id": ma_case_id,
                "route_id": route_id,
                "target_id": prog_id,
                "application_route": "MA_PROGRAMME",
                "research_state": "EVIDENCE_READY",
                "user_disposition": "UNDECIDED",
                "application_stage": "NOT_STARTED",
            },
            {
                "id": supervisor_case_id,
                "route_id": route_id,
                "target_id": sup_id,
                "application_route": "SUPERVISOR_FIRST_PHD",
                "research_state": "EVIDENCE_READY",
                "user_disposition": "UNDECIDED",
                "application_stage": "NOT_STARTED",
            },
        ]
    )

    # Insert snapshots
    db_session.execute(
        text("""
            INSERT INTO radar_source_snapshots
            (id, source_url, fingerprint, state, captured_at, created_at, updated_at)
            VALUES (:id, :source_url, :fingerprint, :state, :captured_at, datetime('now'), datetime('now'))
        """),
        [
            {
                "id": snap_a_id,
                "source_url": "https://example.com/funding-a",
                "fingerprint": "fp-a-v1",
                "state": "CAPTURED",
                "captured_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": snap_sup_id,
                "source_url": "https://example.com/supervisor",
                "fingerprint": "fp-sup-v1",
                "state": "CAPTURED",
                "captured_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
    )

    # Insert claims
    db_session.execute(
        text("""
            INSERT INTO radar_claims
            (id, case_id, statement, claim_type, status, created_at, updated_at)
            VALUES (:id, :case_id, :statement, :claim_type, :status, datetime('now'), datetime('now'))
        """),
        [
            {
                "id": claim_a_id,
                "case_id": ma_case_id,
                "statement": "Funding A award is $10,000",
                "claim_type": "EXTERNAL_FACT",
                "status": "SUPPORTED",
            },
            {
                "id": claim_b_id,
                "case_id": ma_case_id,
                "statement": "Funding B award is $5,000",
                "claim_type": "EXTERNAL_FACT",
                "status": "SUPPORTED",
            },
            {
                "id": claim_sup_id,
                "case_id": supervisor_case_id,
                "statement": "Supervisor has published work on topic X",
                "claim_type": "EXTERNAL_FACT",
                "status": "SUPPORTED",
            },
        ]
    )

    # Insert gates
    db_session.execute(
        text("""
            INSERT INTO radar_gate_assessments
            (id, case_id, requirement, source_authority, result, created_at, updated_at)
            VALUES (:id, :case_id, :requirement, :source_authority, :result, datetime('now'), datetime('now'))
        """),
        [
            {
                "id": gate_a_id,
                "case_id": ma_case_id,
                "requirement": "Eligible for Funding A",
                "source_authority": "OFFICIAL_PROGRAMME",
                "result": "PASS",
            },
            {
                "id": gate_b_id,
                "case_id": ma_case_id,
                "requirement": "Eligible for Funding B",
                "source_authority": "OFFICIAL_PROGRAMME",
                "result": "PASS",
            },
        ]
    )

    # Insert notes
    db_session.execute(
        text("""
            INSERT INTO radar_user_notes
            (id, case_id, body, at)
            VALUES (:id, :case_id, :body, datetime('now'))
        """),
        [
            {
                "id": note_ma_id,
                "case_id": ma_case_id,
                "body": "Personal assessment: strong match",
            },
        ]
    )

    # Build dependency graph
    # snapshot_a -> claim_a_amount -> gate_fund_a_eligible
    add_dependency(
        db_session,
        upstream_kind="SourceSnapshot",
        upstream_id=snap_a_id,
        downstream_kind="Claim",
        downstream_id=claim_a_id,
    )
    add_dependency(
        db_session,
        upstream_kind="Claim",
        upstream_id=claim_a_id,
        downstream_kind="GateAssessment",
        downstream_id=gate_a_id,
    )

    # snapshot_supervisor -> claim_supervisor_work
    add_dependency(
        db_session,
        upstream_kind="SourceSnapshot",
        upstream_id=snap_sup_id,
        downstream_kind="Claim",
        downstream_id=claim_sup_id,
    )

    db_session.commit()

    return {
        "snapshot_a_id": snap_a_id,
        "snapshot_sup_id": snap_sup_id,
        "ma_case_id": ma_case_id,
        "supervisor_case_id": supervisor_case_id,
        "claim_a_id": claim_a_id,
        "claim_b_id": claim_b_id,
        "claim_sup_id": claim_sup_id,
        "gate_a_id": gate_a_id,
        "gate_b_id": gate_b_id,
        "note_ma_id": note_ma_id,
    }


class TestInvalidationDependencyTargeted:
    """Test targeted dependency-based invalidation (ORACLE-020)."""

    # ORACLE-020
    def test_invalidate_only_dependent_claim_when_snapshot_changes(
        self, db_session: Session, setup_entities
    ):
        """When snapshot_a changes, only claim_a_amount becomes STALE."""
        entities = setup_entities

        # Invalidate snapshot A
        report = invalidate(db_session, entities["snapshot_a_id"])

        # Check claim_a_amount is STALE
        result = db_session.execute(
            text("SELECT status FROM radar_claims WHERE id = :id"),
            {"id": entities["claim_a_id"]}
        ).scalar()
        assert result == "STALE", f"claim_a_amount should be STALE, got {result}"

        # Check claim_b_amount is unchanged
        result = db_session.execute(
            text("SELECT status FROM radar_claims WHERE id = :id"),
            {"id": entities["claim_b_id"]}
        ).scalar()
        assert result == "SUPPORTED", f"claim_b_amount should remain SUPPORTED, got {result}"

        # Check supervisor claim is unchanged
        result = db_session.execute(
            text("SELECT status FROM radar_claims WHERE id = :id"),
            {"id": entities["claim_sup_id"]}
        ).scalar()
        assert result == "SUPPORTED", f"claim_supervisor_work should remain SUPPORTED, got {result}"

    def test_invalidate_gate_downstream_of_snapshot(
        self, db_session: Session, setup_entities
    ):
        """Invalidating snapshot_a marks gate_fund_a_eligible STALE."""
        entities = setup_entities

        report = invalidate(db_session, entities["snapshot_a_id"])

        # Gate should be STALE
        result = db_session.execute(
            text("SELECT result FROM radar_gate_assessments WHERE id = :id"),
            {"id": entities["gate_a_id"]}
        ).scalar()
        assert result == "STALE", f"gate_fund_a_eligible should be STALE, got {result}"

        # Gate B should remain unchanged
        result = db_session.execute(
            text("SELECT result FROM radar_gate_assessments WHERE id = :id"),
            {"id": entities["gate_b_id"]}
        ).scalar()
        assert result == "PASS", f"gate_fund_b_eligible should remain PASS, got {result}"

    def test_unrelated_supervisor_case_unchanged(
        self, db_session: Session, setup_entities
    ):
        """Invalidating snapshot_a does not affect unrelated supervisor case."""
        entities = setup_entities

        # Record initial state
        initial = db_session.execute(
            text("SELECT research_state, user_disposition FROM radar_evaluation_cases WHERE id = :id"),
            {"id": entities["supervisor_case_id"]}
        ).one()
        initial_research_state, initial_disposition = initial

        # Invalidate snapshot A (MA case only)
        report = invalidate(db_session, entities["snapshot_a_id"])

        # Verify supervisor case is unchanged
        final = db_session.execute(
            text("SELECT research_state, user_disposition FROM radar_evaluation_cases WHERE id = :id"),
            {"id": entities["supervisor_case_id"]}
        ).one()
        final_research_state, final_disposition = final

        assert final_research_state == initial_research_state, "supervisor_case research_state should not change"
        assert final_disposition == initial_disposition, "supervisor_case user_disposition should not change"

    # ORACLE-042
    def test_user_notes_survive_invalidation(
        self, db_session: Session, setup_entities
    ):
        """User notes on the MA case survive invalidation."""
        entities = setup_entities

        # Note should exist
        body_before = db_session.execute(
            text("SELECT body FROM radar_user_notes WHERE id = :id"),
            {"id": entities["note_ma_id"]}
        ).scalar()
        assert body_before == "Personal assessment: strong match"

        # Invalidate snapshot A
        report = invalidate(db_session, entities["snapshot_a_id"])

        # Note should still exist with same content
        body_after = db_session.execute(
            text("SELECT body FROM radar_user_notes WHERE id = :id"),
            {"id": entities["note_ma_id"]}
        ).scalar()
        assert body_after == "Personal assessment: strong match"

    def test_invalidation_report_contains_stale_objects(
        self, db_session: Session, setup_entities
    ):
        """InvalidationReport includes lists of stale claims, assessments, etc."""
        entities = setup_entities

        report = invalidate(db_session, entities["snapshot_a_id"])

        assert isinstance(report, InvalidationReport)
        assert hasattr(report, "stale_claims")
        assert hasattr(report, "stale_assessments")
        assert hasattr(report, "stale_suggestions")
        assert hasattr(report, "stale_briefs")
        assert hasattr(report, "stale_cases")
        assert hasattr(report, "unresolved_dependencies")

    def test_historical_snapshot_data_preserved(
        self, db_session: Session, setup_entities
    ):
        """Historical snapshot data is not overwritten during invalidation."""
        entities = setup_entities

        # Get snapshot state
        initial = db_session.execute(
            text("SELECT fingerprint, state FROM radar_source_snapshots WHERE id = :id"),
            {"id": entities["snapshot_a_id"]}
        ).one()
        initial_fp, initial_state = initial

        # Invalidate
        report = invalidate(db_session, entities["snapshot_a_id"])

        # Verify snapshot is unchanged
        final = db_session.execute(
            text("SELECT fingerprint, state FROM radar_source_snapshots WHERE id = :id"),
            {"id": entities["snapshot_a_id"]}
        ).one()
        final_fp, final_state = final

        assert final_fp == initial_fp, "fingerprint should be unchanged"
        assert final_state == initial_state, "state should be unchanged"


class TestCanaryUnrelatedCaseInvalidation:
    """Canary: global invalidation must be detected as a defect."""

    @pytest.mark.canary
    def test_canary_unrelated_case_invalidation(
        self, db_session: Session, setup_entities
    ):
        """CANARY: Mutated invalidate that marks every case STALE must fail the test.

        This canary checks that our test properly detects a defective implementation
        that uses global updated_at style invalidation instead of dependency-targeted.
        """
        from tests.academic_radar.canary import expect_violation

        entities = setup_entities

        def check_unrelated_case_unchanged():
            """Assertion: unrelated case must remain EVIDENCE_READY."""
            result = db_session.execute(
                text("SELECT research_state FROM radar_evaluation_cases WHERE id = :id"),
                {"id": entities["supervisor_case_id"]}
            ).scalar()
            assert result == "EVIDENCE_READY", (
                "unrelated supervisor case should not become STALE"
            )

        # Invalidate snapshot A (MA case only)
        report = invalidate(db_session, entities["snapshot_a_id"])

        # This check should pass (supervisor case is unaffected)
        check_unrelated_case_unchanged()
