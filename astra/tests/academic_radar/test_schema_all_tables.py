"""Test that all required schema tables exist after migration."""

import os
import sqlite3
import tempfile
import subprocess
import sys
from pathlib import Path


def test_alembic_upgrade_head_creates_all_tables():
    """Test that alembic upgrade head creates all required tables on empty DB."""
    # Create a temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Set DATABASE_URL for alembic
        db_url = f"sqlite:///{db_path}"
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url

        # Run alembic upgrade head
        astra_dir = Path(__file__).parent.parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(astra_dir),
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"alembic upgrade head failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )

        # Connect to the database and verify all tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all table names
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'radar_%' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {
            "radar_candidate_profiles",
            "radar_candidate_evidence",
            "radar_mozare_routes",
            "radar_target_entities",
            "radar_person_identities",
            "radar_programmes",
            "radar_opportunities",
            "radar_funding_routes",
            "radar_entity_relations",
            "radar_evaluation_cases",
            "radar_case_disposition_history",
            "radar_application_stage_history",
            "radar_user_notes",
            "radar_research_protocols",
            "radar_research_runs",
            "radar_research_coverage",
            "radar_evidence_artifacts",
            "radar_source_snapshots",
            "radar_source_authorities",
            "radar_discovery_traces",
            "radar_evidence_dependencies",
            "radar_claims",
            "radar_claim_evidence",
            "radar_gate_assessments",
            "radar_dimension_assessments",
            "radar_funding_assessments",
            "radar_supervision_precedents",
            "radar_watch_targets",
            "radar_watch_checks",
            "radar_change_events",
            "radar_application_briefs",
            "radar_brief_dependencies",
        }

        missing_tables = required_tables - tables
        assert (
            not missing_tables
        ), f"Missing required tables: {missing_tables}\nFound tables: {tables}"

        # Verify critical columns exist for watch tables
        def get_columns(table_name):
            cursor.execute(f"PRAGMA table_info({table_name})")
            return {row[1] for row in cursor.fetchall()}

        # radar_watch_targets columns
        watch_targets_cols = get_columns("radar_watch_targets")
        assert "id" in watch_targets_cols
        assert "target_id" in watch_targets_cols
        assert "url" in watch_targets_cols
        assert "cadence" in watch_targets_cols
        assert "state" in watch_targets_cols
        assert "created_at" in watch_targets_cols
        assert "updated_at" in watch_targets_cols

        # radar_watch_checks columns
        watch_checks_cols = get_columns("radar_watch_checks")
        assert "id" in watch_checks_cols
        assert "watch_target_id" in watch_checks_cols
        assert "snapshot_id" in watch_checks_cols
        assert "changed" in watch_checks_cols
        assert "at" in watch_checks_cols
        assert "created_at" in watch_checks_cols
        assert "updated_at" in watch_checks_cols

        # radar_change_events columns
        change_events_cols = get_columns("radar_change_events")
        assert "id" in change_events_cols
        assert "watch_check_id" in change_events_cols
        assert "summary" in change_events_cols
        assert "material" in change_events_cols
        assert "at" in change_events_cols
        assert "created_at" in change_events_cols
        assert "updated_at" in change_events_cols

        # radar_application_briefs columns
        briefs_cols = get_columns("radar_application_briefs")
        assert "id" in briefs_cols
        assert "case_id" in briefs_cols
        assert "frozen_at" in briefs_cols
        assert "content" in briefs_cols
        assert "state" in briefs_cols
        assert "superseded_by" in briefs_cols
        assert "created_at" in briefs_cols
        assert "updated_at" in briefs_cols

        # radar_brief_dependencies columns
        deps_cols = get_columns("radar_brief_dependencies")
        assert "id" in deps_cols
        assert "brief_id" in deps_cols
        assert "dependency_kind" in deps_cols
        assert "dependency_id" in deps_cols
        assert "dependency_version" in deps_cols
        assert "created_at" in deps_cols
        assert "updated_at" in deps_cols

        conn.close()

    finally:
        # Clean up the temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_alembic_has_single_head():
    """Test that alembic has exactly one head revision."""
    astra_dir = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=str(astra_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"alembic heads failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    # Count the number of head revisions
    heads = result.stdout.strip().split("\n")
    heads = [h for h in heads if h.strip()]
    assert len(heads) == 1, f"Expected exactly 1 head, got {len(heads)}: {heads}"
