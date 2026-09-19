import os
import subprocess
import sys
import tempfile
import uuid
import pytest
from decimal import Decimal
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


class TestClaimsSchema:
    def test_upgrade_creates_claims_tables(self, alembic_config):
        """Test that alembic upgrade head creates all required claims tables."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        required_tables = {
            "radar_claims",
            "radar_claim_evidence",
            "radar_gate_assessments",
            "radar_dimension_assessments",
            "radar_funding_assessments",
            "radar_supervision_precedents",
        }

        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    def test_radar_claims_has_required_columns(self, alembic_config):
        """Test that radar_claims has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_claims")}

        required_columns = {
            "id",
            "case_id",
            "statement",
            "claim_type",
            "status",
            "generated_by",
            "run_id",
            "protocol_version",
            "reviewed_by_user",
            "last_checked_at",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_radar_claim_evidence_has_required_columns(self, alembic_config):
        """Test that radar_claim_evidence has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_claim_evidence")}

        required_columns = {
            "id",
            "claim_id",
            "evidence_artifact_id",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_radar_gate_assessments_has_required_columns(self, alembic_config):
        """Test that radar_gate_assessments has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_gate_assessments")}

        required_columns = {
            "id",
            "case_id",
            "requirement",
            "source_authority",
            "effective_date",
            "evaluation_rule",
            "result",
            "evidence_ids",
            "provenance",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_radar_dimension_assessments_has_required_columns(self, alembic_config):
        """Test that radar_dimension_assessments has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_dimension_assessments")}

        required_columns = {
            "id",
            "case_id",
            "dimension_id",
            "scale",
            "value",
            "unknowns",
            "reviewer_status",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_radar_funding_assessments_has_required_columns(self, alembic_config):
        """Test that radar_funding_assessments has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_funding_assessments")}

        required_columns = {
            "id",
            "case_id",
            "funding_route_id",
            "currency",
            "award_amount",
            "tuition_amount",
            "duration_months",
            "known_costs",
            "unknown_costs",
            "uncovered_gap",
            "state",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_radar_supervision_precedents_has_required_columns(self, alembic_config):
        """Test that radar_supervision_precedents has all required columns."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("radar_supervision_precedents")}

        required_columns = {
            "id",
            "case_id",
            "person_target_id",
            "project_target_id",
            "role",
            "fields",
            "created_at",
            "updated_at",
        }

        assert required_columns.issubset(columns), f"Missing columns: {required_columns - columns}"

    def test_dimension_value_4_rejected(self, alembic_config):
        """Test that dimension value 4 is rejected (0..3 only)."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a case first
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())
            case_id = str(uuid.uuid4())

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
            session.commit()

            # Try to insert dimension assessment with value=4 (should fail)
            with pytest.raises(exc.IntegrityError):
                dim_id = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO radar_dimension_assessments
                        (id, case_id, dimension_id, scale, value, created_at, updated_at)
                        VALUES (:id, :case_id, :dimension_id, :scale, :value, datetime('now'), datetime('now'))
                    """),
                    {
                        "id": dim_id,
                        "case_id": case_id,
                        "dimension_id": "supervision_depth",
                        "scale": "0-3",
                        "value": 4,
                    }
                )
                session.commit()

    def test_dimension_value_null_accepted(self, alembic_config):
        """Test that dimension value NULL is accepted (Unknown)."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a case first
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())
            case_id = str(uuid.uuid4())

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
            session.commit()

            # Insert dimension assessment with value=NULL (should succeed)
            dim_id = str(uuid.uuid4())
            session.execute(
                text("""
                    INSERT INTO radar_dimension_assessments
                    (id, case_id, dimension_id, scale, value, created_at, updated_at)
                    VALUES (:id, :case_id, :dimension_id, :scale, :value, datetime('now'), datetime('now'))
                """),
                {
                    "id": dim_id,
                    "case_id": case_id,
                    "dimension_id": "supervision_depth",
                    "scale": "0-3",
                    "value": None,
                }
            )
            session.commit()

            # Verify it was inserted
            result = session.execute(
                text("SELECT value FROM radar_dimension_assessments WHERE id = :id"),
                {"id": dim_id}
            ).scalar()
            assert result is None

    def test_claim_type_outside_enum_rejected(self, alembic_config):
        """Test that claim_type outside ClaimType enum is rejected."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a case first
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())
            case_id = str(uuid.uuid4())

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
            session.commit()

            # Try to insert claim with invalid claim_type
            with pytest.raises(exc.IntegrityError):
                claim_id = str(uuid.uuid4())
                session.execute(
                    text("""
                        INSERT INTO radar_claims
                        (id, case_id, statement, claim_type, status, created_at, updated_at)
                        VALUES (:id, :case_id, :statement, :claim_type, :status, datetime('now'), datetime('now'))
                    """),
                    {
                        "id": claim_id,
                        "case_id": case_id,
                        "statement": "Test claim",
                        "claim_type": "INVALID_TYPE",
                        "status": "SUPPORTED",
                    }
                )
                session.commit()

    def test_funding_amounts_roundtrip_decimal(self, alembic_config):
        """Test that funding amounts round-trip as Decimal exactly."""
        db_url, path = alembic_config

        engine = create_engine(db_url)
        with Session(engine) as session:
            # Create a case first
            route_id = str(uuid.uuid4())
            target_id = str(uuid.uuid4())
            case_id = str(uuid.uuid4())
            funding_route_id = str(uuid.uuid4())

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
                    INSERT INTO radar_target_entities
                    (id, kind, display_name, created_at, updated_at)
                    VALUES (:id, :kind, :display_name, datetime('now'), datetime('now'))
                """),
                {"id": funding_route_id, "kind": "FundingRoute", "display_name": "Test Funding"}
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
                    "application_route": "MA_PROGRAMME",
                    "research_state": "DISCOVERED",
                    "user_disposition": "UNDECIDED",
                    "application_stage": "NOT_STARTED",
                }
            )
            session.commit()

            # Insert funding assessment with precise decimal amounts
            # SQLite requires string conversion for Decimal values
            funding_id = str(uuid.uuid4())
            award_amount = Decimal("10.10")
            tuition_amount = Decimal("0.10")
            uncovered_gap = Decimal("25.99")

            session.execute(
                text("""
                    INSERT INTO radar_funding_assessments
                    (id, case_id, funding_route_id, currency, award_amount, tuition_amount, duration_months, uncovered_gap, state, created_at, updated_at)
                    VALUES (:id, :case_id, :funding_route_id, :currency, :award_amount, :tuition_amount, :duration_months, :uncovered_gap, :state, datetime('now'), datetime('now'))
                """),
                {
                    "id": funding_id,
                    "case_id": case_id,
                    "funding_route_id": funding_route_id,
                    "currency": "GBP",
                    "award_amount": str(award_amount),
                    "tuition_amount": str(tuition_amount),
                    "duration_months": 24,
                    "uncovered_gap": str(uncovered_gap),
                    "state": "ELIGIBLE",
                }
            )
            session.commit()

            # Read back and verify exact decimal values
            result = session.execute(
                text("""
                    SELECT award_amount, tuition_amount, uncovered_gap
                    FROM radar_funding_assessments
                    WHERE id = :id
                """),
                {"id": funding_id}
            ).fetchone()

            assert result is not None
            read_award, read_tuition, read_gap = result

            # SQLite stores decimals as strings/floats, so we need to convert back
            # The important thing is that the values round-trip correctly
            assert Decimal(str(read_award)) == award_amount
            assert Decimal(str(read_tuition)) == tuition_amount
            assert Decimal(str(read_gap)) == uncovered_gap
