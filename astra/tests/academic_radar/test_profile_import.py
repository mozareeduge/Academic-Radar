"""Tests for profile and route seed importer."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from academic_radar.profile.mozare_import import import_seed, ImportReport
from tests.academic_radar.canary import expect_violation


def make_temp_db():
    """Create a temporary SQLite database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    normalized_path = path.replace("\\", "/")
    return f"sqlite:///{normalized_path}", path


@pytest.fixture
def alembic_config():
    """Create a fresh temp database with alembic migrations applied."""
    db_url, path = make_temp_db()
    try:
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url
        astra_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=env,
            cwd=astra_dir,
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


@pytest.fixture
def fixture_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


class TestProfileImport:
    """Test profile and route seed importer."""

    def test_import_creates_profile_and_routes(self, alembic_config, fixture_dir):
        """Test that importing synthetic seed creates 1 profile and 2 routes."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        with Session(engine) as session:
            seed_path = fixture_dir / "synthetic_seed.yaml"
            assert seed_path.exists(), f"Fixture not found: {seed_path}"

            report = import_seed(seed_path, session)

        assert report.profiles_created == 1, f"Expected 1 profile created, got {report.profiles_created}"
        assert report.routes_created == 2, f"Expected 2 routes created, got {report.routes_created}"
        assert not report.errors, f"Unexpected errors: {report.errors}"

        # Verify in database
        engine = create_engine(db_url)
        with engine.connect() as conn:
            profile_count = conn.execute(
                text("SELECT COUNT(*) FROM radar_candidate_profiles WHERE state = 'ACTIVE'")
            ).scalar()
            route_count = conn.execute(
                text("SELECT COUNT(*) FROM radar_mozare_routes")
            ).scalar()

            assert profile_count == 1, f"Expected 1 active profile in DB, got {profile_count}"
            assert route_count == 2, f"Expected 2 routes in DB, got {route_count}"

    def test_import_is_idempotent(self, alembic_config, fixture_dir):
        """Test that importing the same file twice creates no duplicates."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        seed_path = fixture_dir / "synthetic_seed.yaml"

        # First import
        with Session(engine) as session:
            report1 = import_seed(seed_path, session)

        assert report1.profiles_created == 1
        assert report1.routes_created == 2

        # Second import
        with Session(engine) as session:
            report2 = import_seed(seed_path, session)

        # Should update, not create
        assert report2.profiles_created == 0, f"Expected 0 new profiles on second import, got {report2.profiles_created}"
        assert report2.profiles_updated == 1, f"Expected 1 updated profile, got {report2.profiles_updated}"
        assert report2.routes_created == 0, f"Expected 0 new routes on second import, got {report2.routes_created}"
        assert report2.routes_updated == 2, f"Expected 2 updated routes, got {report2.routes_updated}"

        # Verify totals in database remain the same
        engine = create_engine(db_url)
        with engine.connect() as conn:
            profile_count = conn.execute(
                text("SELECT COUNT(*) FROM radar_candidate_profiles WHERE state = 'ACTIVE'")
            ).scalar()
            route_count = conn.execute(
                text("SELECT COUNT(*) FROM radar_mozare_routes")
            ).scalar()

            assert profile_count == 1, f"Expected 1 active profile in DB after second import, got {profile_count}"
            assert route_count == 2, f"Expected 2 routes in DB after second import, got {route_count}"

    def test_missing_provenance_raises_error(self, alembic_config, tmp_path):
        """Test that missing provenance raises ValueError."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        # Create seed file with missing provenance
        bad_seed = tmp_path / "bad_seed.yaml"
        bad_seed.write_text("""
candidate:
  state: ACTIVE
  fixed_constraints:
    value: "Some constraint without provenance"
routes: []
""")

        with Session(engine) as session:
            with pytest.raises(ValueError, match="missing required 'provenance'"):
                import_seed(bad_seed, session)

    def test_invalid_profile_state_raises_error(self, alembic_config, tmp_path):
        """Test that invalid ProfileState raises ValueError."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        bad_seed = tmp_path / "bad_state.yaml"
        bad_seed.write_text("""
candidate:
  state: INVALID_STATE
  fixed_constraints:
    provenance:
      source: "test"
      verified: true
    value: "test"
routes: []
""")

        with Session(engine) as session:
            with pytest.raises(ValueError, match="Invalid profile state"):
                import_seed(bad_seed, session)

    def test_invalid_route_state_raises_error(self, alembic_config, tmp_path):
        """Test that invalid RouteState raises ValueError."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        bad_seed = tmp_path / "bad_route_state.yaml"
        bad_seed.write_text("""
candidate:
routes:
  - seed_key: "test-route"
    state: INVALID_ROUTE_STATE
""")

        with Session(engine) as session:
            with pytest.raises(ValueError, match="Invalid route state"):
                import_seed(bad_seed, session)

    def test_missing_seed_key_in_route_raises_error(self, alembic_config, tmp_path):
        """Test that route without seed_key raises ValueError."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        bad_seed = tmp_path / "no_seed_key.yaml"
        bad_seed.write_text("""
candidate:
routes:
  - name: "Test Route"
    state: ACTIVE
""")

        with Session(engine) as session:
            with pytest.raises(ValueError, match="seed_key"):
                import_seed(bad_seed, session)

    def test_file_not_found_raises_error(self, alembic_config):
        """Test that missing file raises FileNotFoundError."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        with Session(engine) as session:
            with pytest.raises(FileNotFoundError):
                import_seed("/nonexistent/path/seed.yaml", session)

    def test_report_structure(self, alembic_config, fixture_dir):
        """Test that ImportReport has expected structure."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        with Session(engine) as session:
            seed_path = fixture_dir / "synthetic_seed.yaml"
            report = import_seed(seed_path, session)

        assert isinstance(report, ImportReport)
        assert hasattr(report, "profiles_created")
        assert hasattr(report, "profiles_updated")
        assert hasattr(report, "routes_created")
        assert hasattr(report, "routes_updated")
        assert hasattr(report, "errors")
        assert isinstance(report.errors, list)

    def test_profile_data_persists(self, alembic_config, fixture_dir):
        """Test that profile data is correctly persisted."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        with Session(engine) as session:
            seed_path = fixture_dir / "synthetic_seed.yaml"
            import_seed(seed_path, session)

        # Verify profile data in database
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT state, fixed_constraints, education, language_evidence,
                           scholarly_work, artistic_curatorial_work,
                           professional_technical_evidence
                    FROM radar_candidate_profiles
                    WHERE state = 'ACTIVE'
                """)
            ).first()

            assert result is not None, "No active profile found"
            state, constraints, education, language, scholarly, artistic, professional = result

            assert state == "ACTIVE"
            assert constraints is not None
            assert education is not None
            assert language is not None
            assert scholarly is not None
            assert artistic is not None
            assert professional is not None

    def test_route_data_persists(self, alembic_config, fixture_dir):
        """Test that route data is correctly persisted."""
        db_url, path = alembic_config
        engine = create_engine(db_url)

        with Session(engine) as session:
            seed_path = fixture_dir / "synthetic_seed.yaml"
            import_seed(seed_path, session)

        # Verify routes in database
        with engine.connect() as conn:
            results = conn.execute(
                text("""
                    SELECT name, state, route_statement, core_problem,
                           operations_methods, target_disciplines, maturity
                    FROM radar_mozare_routes
                    ORDER BY name
                """)
            ).fetchall()

            assert len(results) == 2, f"Expected 2 routes, got {len(results)}"

            # Check first route
            name1, state1, stmt1, problem1, methods1, disciplines1, maturity1 = results[0]
            assert name1 == "computational-physics-phd"
            assert state1 == "ACTIVE"
            assert stmt1 is not None
            assert problem1 is not None

            # Check second route
            name2, state2, stmt2, problem2, methods2, disciplines2, maturity2 = results[1]
            assert name2 == "quantum-simulation-route"
            assert state2 == "ACTIVE"
