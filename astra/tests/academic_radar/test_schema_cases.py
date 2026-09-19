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


class TestCasesSchema:
    def test_upgrade_creates_cases_tables(self, alembic_config):
        """Test that alembic upgrade head creates all required case tables."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        required_tables = {
            "radar_evaluation_cases",
            "radar_case_disposition_history",
            "radar_application_stage_history",
            "radar_user_notes",
        }

        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    def test_evaluation_cases_has_required_columns(self, alembic_config):
        """Test that radar_evaluation_cases has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_evaluation_cases")}

        required_columns = {
            "id",
            "route_id",
            "target_id",
            "application_route",
            "research_state",
            "user_disposition",
            "suggested_disposition",
            "application_stage",
            "next_action",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_case_disposition_history_has_required_columns(self, alembic_config):
        """Test that radar_case_disposition_history has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_case_disposition_history")}

        required_columns = {
            "id",
            "case_id",
            "previous",
            "new",
            "actor",
            "reason",
            "at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_application_stage_history_has_required_columns(self, alembic_config):
        """Test that radar_application_stage_history has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_application_stage_history")}

        required_columns = {
            "id",
            "case_id",
            "previous",
            "new",
            "at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_user_notes_has_required_columns(self, alembic_config):
        """Test that radar_user_notes has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_user_notes")}

        required_columns = {
            "id",
            "case_id",
            "body",
            "at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_duplicate_case_identity_rejected(self, alembic_config):
        """Test that two evaluation cases with same (route, target, application_route) are rejected."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # First create a route and target
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

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
            session.commit()

            # Insert first case
            case_id1 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_evaluation_cases
                    (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
                    VALUES (:id, :route_id, :target_id, :application_route, :research_state, :user_disposition, :application_stage, datetime('now'), datetime('now'))
                """),
                {
                    "id": case_id1,
                    "route_id": route_id,
                    "target_id": target_id,
                    "application_route": "SUPERVISOR_FIRST_PHD",
                    "research_state": "DISCOVERED",
                    "user_disposition": "UNDECIDED",
                    "application_stage": "NOT_STARTED",
                }
            )
            session.commit()

            # Try to insert duplicate
            with pytest.raises(exc.IntegrityError):
                case_id2 = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO radar_evaluation_cases
                        (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
                        VALUES (:id, :route_id, :target_id, :application_route, :research_state, :user_disposition, :application_stage, datetime('now'), datetime('now'))
                    """),
                    {
                        "id": case_id2,
                        "route_id": route_id,
                        "target_id": target_id,
                        "application_route": "SUPERVISOR_FIRST_PHD",
                        "research_state": "DISCOVERED",
                        "user_disposition": "UNDECIDED",
                        "application_stage": "NOT_STARTED",
                    }
                )
                session.commit()

    def test_same_route_target_different_application_route_allowed(self, alembic_config):
        """Test that same route+target with different application_route is allowed."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a route and target
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

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
            session.commit()

            # Insert first case with SUPERVISOR_FIRST_PHD
            case_id1 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_evaluation_cases
                    (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
                    VALUES (:id, :route_id, :target_id, :application_route, :research_state, :user_disposition, :application_stage, datetime('now'), datetime('now'))
                """),
                {
                    "id": case_id1,
                    "route_id": route_id,
                    "target_id": target_id,
                    "application_route": "SUPERVISOR_FIRST_PHD",
                    "research_state": "DISCOVERED",
                    "user_disposition": "UNDECIDED",
                    "application_stage": "NOT_STARTED",
                }
            )
            session.commit()

            # Insert second case with same route+target but different application_route (MA_PROGRAMME)
            case_id2 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_evaluation_cases
                    (id, route_id, target_id, application_route, research_state, user_disposition, application_stage, created_at, updated_at)
                    VALUES (:id, :route_id, :target_id, :application_route, :research_state, :user_disposition, :application_stage, datetime('now'), datetime('now'))
                """),
                {
                    "id": case_id2,
                    "route_id": route_id,
                    "target_id": target_id,
                    "application_route": "MA_PROGRAMME",
                    "research_state": "DISCOVERED",
                    "user_disposition": "UNDECIDED",
                    "application_stage": "NOT_STARTED",
                }
            )
            session.commit()

            result = session.execute(
                text("SELECT COUNT(*) FROM radar_evaluation_cases WHERE route_id = :route_id AND target_id = :target_id"),
                {"route_id": route_id, "target_id": target_id}
            ).scalar()
            assert result == 2

    def test_user_disposition_rejects_invalid_value(self, alembic_config):
        """Test that user_disposition rejects values outside UserDisposition enum."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a route and target
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

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
            session.commit()

            # Try to insert case with invalid user_disposition
            with pytest.raises(exc.IntegrityError):
                case_id = str(uuid.uuid4())
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
                        "user_disposition": "INVALID_DISPOSITION",
                        "application_stage": "NOT_STARTED",
                    }
                )
                session.commit()

    def test_research_state_rejects_undecided(self, alembic_config):
        """Test that research_state rejects UNDECIDED value."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a route and target
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())

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
            session.commit()

            # Try to insert case with UNDECIDED as research_state (which is invalid)
            with pytest.raises(exc.IntegrityError):
                case_id = str(uuid.uuid4())
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
                        "research_state": "UNDECIDED",
                        "user_disposition": "UNDECIDED",
                        "application_stage": "NOT_STARTED",
                    }
                )
                session.commit()
