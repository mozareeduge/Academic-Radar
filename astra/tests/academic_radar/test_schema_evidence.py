import os
import subprocess
import sys
import tempfile
import uuid
import pytest
from sqlalchemy import create_engine, inspect, exc, text
from sqlalchemy.orm import Session


def make_temp_db():
    """Create a temporary SQLite database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    # Convert to forward slashes for SQLite URL on Windows
    normalized_path = path.replace("\\", "/")
    return f"sqlite:///{normalized_path}", path


@pytest.fixture
def temp_db_pair():
    """Create a temporary SQLite database for testing."""
    db_url, path = make_temp_db()
    yield db_url, path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def alembic_config():
    """Create a fresh temp database with alembic migrations applied."""
    db_url, path = make_temp_db()
    try:
        # Run alembic in a subprocess to avoid state issues
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
        yield db_url, path
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


class TestEvidenceSchema:
    def test_upgrade_creates_evidence_tables(self, alembic_config):
        """Test that alembic upgrade head creates all required evidence tables."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        required_tables = {
            "radar_research_protocols",
            "radar_research_runs",
            "radar_research_coverage",
            "radar_evidence_artifacts",
            "radar_source_snapshots",
            "radar_source_authorities",
            "radar_discovery_traces",
            "radar_evidence_dependencies",
        }

        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    def test_research_protocols_has_required_columns(self, alembic_config):
        """Test that radar_research_protocols has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_research_protocols")}

        required_columns = {
            "id",
            "application_route",
            "protocol_version",
            "definition",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_research_runs_has_required_columns(self, alembic_config):
        """Test that radar_research_runs has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_research_runs")}

        required_columns = {
            "id",
            "case_id",
            "protocol_version",
            "model_id",
            "provider_id",
            "prompt_hash",
            "schema_version",
            "run_identity",
            "status",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_research_coverage_has_required_columns(self, alembic_config):
        """Test that radar_research_coverage has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_research_coverage")}

        required_columns = {
            "id",
            "run_id",
            "evidence_class",
            "status",
            "evidence_ids",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_evidence_artifacts_has_required_columns(self, alembic_config):
        """Test that radar_evidence_artifacts has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_evidence_artifacts")}

        required_columns = {
            "id",
            "source_url",
            "source_type",
            "excerpt",
            "structured_extraction",
            "snapshot_id",
            "retrieved_at",
            "published_at",
            "source_authority",
            "canonical_origin",
            "identity_confidence",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_source_snapshots_has_required_columns(self, alembic_config):
        """Test that radar_source_snapshots has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_source_snapshots")}

        required_columns = {
            "id",
            "source_url",
            "fingerprint",
            "state",
            "content_ref",
            "captured_at",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_source_authorities_has_required_columns(self, alembic_config):
        """Test that radar_source_authorities has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_source_authorities")}

        required_columns = {
            "id",
            "host_pattern",
            "authority",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_discovery_traces_has_required_columns(self, alembic_config):
        """Test that radar_discovery_traces has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_discovery_traces")}

        required_columns = {
            "id",
            "target_id",
            "source",
            "query",
            "run_id",
            "at",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_evidence_dependencies_has_required_columns(self, alembic_config):
        """Test that radar_evidence_dependencies has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_evidence_dependencies")}

        required_columns = {
            "id",
            "upstream_kind",
            "upstream_id",
            "downstream_kind",
            "downstream_id",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_research_coverage_rejects_invalid_status(self, alembic_config):
        """Test that research_coverage rejects a status outside CoverageStatus enum."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a case and run
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())
            case_id = str(uuid.uuid4())
            run_id = str(uuid.uuid4())

            session.execute(
                text("""
                    INSERT INTO radar_mozare_routes
                    (id, name, state, created_at, updated_at)
                    VALUES (:id, :name, :state, datetime('now'), datetime('now'))
                """),
                {"id": route_id, "name": "Test Route", "state": "ACTIVE"}
            )
            session.execute(
                text("""
                    INSERT INTO radar_target_entities
                    (id, kind, display_name, created_at, updated_at)
                    VALUES (:id, :kind, :display_name, datetime('now'), datetime('now'))
                """),
                {"id": target_id, "kind": "Person", "display_name": "Test Person"}
            )
            session.execute(
                text("""
                    INSERT INTO radar_evaluation_cases
                    (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
                    VALUES (:id, :route_id, :target_id, :application_route, :research_state, :user_disposition, :application_stage, datetime('now'), datetime('now'))
                """),
                {
                    "id": case_id,
                    "route_id": route_id,
                    "target_id": target_id,
                    "application_route": "SUPERVISOR_FIRST_PHD",
                    "research_state": "DISCOVERED",
                    "user_disposition": "UNDECIDED",
                    "application_stage": "NOT_STARTED",
                }
            )
            session.execute(
                text("""
                    INSERT INTO radar_research_runs
                    (id, case_id, protocol_version, status, created_at, updated_at)
                    VALUES (:id, :case_id, :protocol_version, :status, datetime('now'), datetime('now'))
                """),
                {
                    "id": run_id,
                    "case_id": case_id,
                    "protocol_version": "1.0.0",
                    "status": "COMPLETED",
                }
            )
            session.commit()

            # Try to insert coverage with invalid status
            with pytest.raises(exc.IntegrityError):
                coverage_id = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO radar_research_coverage
                        (id, run_id, evidence_class, status, created_at, updated_at)
                        VALUES (:id, :run_id, :evidence_class, :status, datetime('now'), datetime('now'))
                    """),
                    {
                        "id": coverage_id,
                        "run_id": run_id,
                        "evidence_class": "SUPERVISOR",
                        "status": "INVALID_STATUS",
                    }
                )
                session.commit()

    def test_protocols_same_route_version_conflict(self, alembic_config):
        """Test that two protocols with same route+version conflict."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Insert first protocol
            protocol_id1 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_research_protocols
                    (id, application_route, protocol_version, created_at, updated_at)
                    VALUES (:id, :application_route, :protocol_version, datetime('now'), datetime('now'))
                """),
                {
                    "id": protocol_id1,
                    "application_route": "SUPERVISOR_FIRST_PHD",
                    "protocol_version": "1.0.0",
                }
            )
            session.commit()

            # Try to insert duplicate
            with pytest.raises(exc.IntegrityError):
                protocol_id2 = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO radar_research_protocols
                        (id, application_route, protocol_version, created_at, updated_at)
                        VALUES (:id, :application_route, :protocol_version, datetime('now'), datetime('now'))
                    """),
                    {
                        "id": protocol_id2,
                        "application_route": "SUPERVISOR_FIRST_PHD",
                        "protocol_version": "1.0.0",
                    }
                )
                session.commit()

    def test_snapshot_same_url_history_allowed(self, alembic_config):
        """Test that a snapshot row can be inserted twice for the same url (history)."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            url = "https://example.com/test"

            # Insert first snapshot
            snapshot_id1 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_source_snapshots
                    (id, source_url, state, captured_at, created_at, updated_at)
                    VALUES (:id, :source_url, :state, datetime('now'), datetime('now'), datetime('now'))
                """),
                {
                    "id": snapshot_id1,
                    "source_url": url,
                    "state": "CAPTURED",
                }
            )
            session.commit()

            # Insert second snapshot for same URL (should succeed - history)
            snapshot_id2 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_source_snapshots
                    (id, source_url, state, captured_at, created_at, updated_at)
                    VALUES (:id, :source_url, :state, datetime('now'), datetime('now'), datetime('now'))
                """),
                {
                    "id": snapshot_id2,
                    "source_url": url,
                    "state": "UNCHANGED",
                }
            )
            session.commit()

            # Verify both rows exist
            result = session.execute(
                text("SELECT COUNT(*) FROM radar_source_snapshots WHERE source_url = :url"),
                {"url": url}
            ).scalar()
            assert result == 2
