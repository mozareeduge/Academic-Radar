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


class TestTargetSchema:
    def test_upgrade_empty_db_creates_all_tables(self, alembic_config):
        """Test that alembic upgrade head creates all required tables on empty DB."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

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
        }

        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    def test_target_entities_has_required_columns(self, alembic_config):
        """Test that radar_target_entities has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_target_entities")}

        required_columns = {
            "id",
            "kind",
            "display_name",
            "canonical_url",
            "doi",
            "orcid",
            "openalex_id",
            "openaire_id",
            "ror",
            "attributes",
            "source_authority",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_person_identities_has_required_columns(self, alembic_config):
        """Test that radar_person_identities has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_person_identities")}

        required_columns = {
            "id",
            "target_entity_id",
            "identity_status",
            "resolution_basis",
            "candidate_set",
            "institution_target_id",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_entity_relations_has_required_columns(self, alembic_config):
        """Test that radar_entity_relations has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_entity_relations")}

        required_columns = {
            "id",
            "subject_id",
            "predicate",
            "object_id",
            "evidence_ids",
            "identity_resolved",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_opportunities_has_application_route_check_constraint(self, alembic_config):
        """Test that radar_opportunities has application_route column with check constraint."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_opportunities")}

        assert "application_route" in columns

    def test_deadline_columns_on_opportunities(self, alembic_config):
        """Test that deadline columns exist on radar_opportunities."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_opportunities")}

        deadline_columns = {
            "deadline_original_text",
            "deadline_date",
            "deadline_local_time",
            "deadline_timezone",
            "deadline_utc",
            "deadline_precision",
            "deadline_evidence_id",
            "deadline_last_checked_at",
        }

        assert deadline_columns.issubset(columns), f"Missing deadline columns: {deadline_columns - columns}"

    def test_same_display_name_different_entities_allowed(self, alembic_config):
        """Test that two target_entities with same display_name can be inserted."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            id1 = str(uuid.uuid4())
            id2 = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_target_entities
                    (id, kind, display_name, created_at, updated_at)
                    VALUES (:id, :kind, :display_name, datetime('now'), datetime('now'))
                """),
                {"id": id1, "kind": "Person", "display_name": "Jane Smith"}
            )
            session.execute(
                text("""
                    INSERT INTO radar_target_entities
                    (id, kind, display_name, created_at, updated_at)
                    VALUES (:id, :kind, :display_name, datetime('now'), datetime('now'))
                """),
                {"id": id2, "kind": "Person", "display_name": "Jane Smith"}
            )
            session.commit()

            result = session.execute(
                text("SELECT COUNT(*) FROM radar_target_entities WHERE display_name = 'Jane Smith'")
            ).scalar()
            assert result == 2

    def test_duplicate_orcid_rejected(self, alembic_config):
        """Test that two target_entities with same non-null orcid cannot be inserted."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            session.execute(
                text("""
                    INSERT INTO radar_target_entities
                    (id, kind, display_name, orcid, created_at, updated_at)
                    VALUES (:id, :kind, :display_name, :orcid, datetime('now'), datetime('now'))
                """),
                {"id": str(uuid.uuid4()), "kind": "Person", "display_name": "Jane Smith", "orcid": "0000-0001-2345-6789"}
            )
            session.commit()

            with pytest.raises(exc.IntegrityError):
                session.execute(
                    text("""
                        INSERT INTO radar_target_entities
                        (id, kind, display_name, orcid, created_at, updated_at)
                        VALUES (:id, :kind, :display_name, :orcid, datetime('now'), datetime('now'))
                    """),
                    {"id": str(uuid.uuid4()), "kind": "Person", "display_name": "John Doe", "orcid": "0000-0001-2345-6789"}
                )
                session.commit()

    def test_invalid_application_route_rejected(self, alembic_config):
        """Test that invalid application_route value is rejected."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            with pytest.raises(exc.IntegrityError):
                session.execute(
                    text("""
                        INSERT INTO radar_opportunities
                        (id, target_entity_id, display_name, application_route, created_at, updated_at)
                        VALUES (:id, :target_entity_id, :display_name, :application_route, datetime('now'), datetime('now'))
                    """),
                    {"id": str(uuid.uuid4()), "target_entity_id": str(uuid.uuid4()), "display_name": "Test Programme", "application_route": "INVALID_ROUTE"}
                )
                session.commit()
