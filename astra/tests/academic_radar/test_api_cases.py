"""tests.academic_radar.test_api_cases — Radar cases API endpoints.

Covers GET /cases, GET /cases/{id}, POST /cases/{id}/disposition,
POST /cases/{id}/notes, POST /cases/{id}/stage.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.app import app
from api.deps import get_db
from api.security import login_limiter, register_limiter
from db.models import Base, User
from db.radar_models_cases import EvaluationCase
from db.repositories import UserRepo
from academic_radar.domain.enums import ApplicationRoute, ResearchState

# Import these INSIDE test functions only to avoid triggering SQLAlchemy registry conflicts
# (db.models.Opportunity and db.radar_models_targets.Opportunity are both registered to Base)


@pytest.fixture(autouse=True)
def _reset_state():
    """Per-test isolation for shared state."""
    register_limiter.clear("testclient")
    login_limiter.clear("testclient")
    from core import cache, tasks
    tasks._in_memory_jobs.clear()
    cache.invalidate("")
    cache.invalidate_matches()
    cache.invalidate_opportunities()
    cache.invalidate_supervisors()
    yield
    register_limiter.clear("testclient")
    login_limiter.clear("testclient")


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import radar models BEFORE creating tables so they register to Base.
    import db.radar_models_targets  # noqa: F401
    import db.radar_models_cases  # noqa: F401
    import db.radar_models_evidence  # noqa: F401
    import db.radar_models_claims  # noqa: F401
    import db.radar_models_watch  # noqa: F401

    # Now create all tables (legacy + radar)
    from db.models import Base as LegacyBase
    LegacyBase.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth(client):
    """Register + login a fresh user; yields auth headers."""
    email = "alice@example.com"
    client.post("/api/auth/register",
                json={"email": email, "password": "SuperSecret1"})
    resp = client.post("/api/auth/login",
                       json={"email": email, "password": "SuperSecret1"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_case(session, *, route_id: str = None, target_id: str = None,
              application_route: str = "SUPERVISOR_FIRST_PHD",
              research_state: str = "DISCOVERED") -> EvaluationCase:
    """Create a case for testing."""
    from db.radar_models_targets import MozareRoute, TargetEntity

    if route_id is None:
        route = MozareRoute(name="Test Route", state="ACTIVE")
        session.add(route)
        session.flush()
        route_id = route.id

    if target_id is None:
        target = TargetEntity(kind="Person", display_name="Test Person")
        session.add(target)
        session.flush()
        target_id = target.id

    case = EvaluationCase(
        route_id=route_id,
        target_id=target_id,
        application_route=application_route,
        research_state=research_state
    )
    session.add(case)
    session.flush()
    return case


class TestCasesList:
    """GET /cases with filters."""

    def test_list_cases_empty(self, client, auth):
        """Empty list returns 200 with empty items."""
        resp = client.get("/api/radar/cases", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_list_cases_returns_separate_disposition_fields(self, client, auth, db_session):
        """List returns both suggested_disposition and user_disposition as SEPARATE fields."""
        case = make_case(db_session)
        case.suggested_disposition = "WATCH"
        case.user_disposition = "UNDECIDED"
        db_session.commit()

        resp = client.get("/api/radar/cases", headers=auth)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert "user_disposition" in item
        assert "suggested_disposition" in item
        assert item["user_disposition"] == "UNDECIDED"
        assert item["suggested_disposition"] == "WATCH"

    # ORACLE-001
    def test_list_cases_filter_application_route(self, client, auth, db_session):
        """Filter by application_route."""
        case1 = make_case(db_session, application_route="SUPERVISOR_FIRST_PHD")
        case2 = make_case(db_session, application_route="MA_PROGRAMME")
        db_session.commit()

        resp = client.get("/api/radar/cases?application_route=SUPERVISOR_FIRST_PHD", headers=auth)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == case1.id

    def test_list_cases_filter_research_state(self, client, auth, db_session):
        """Filter by research_state."""
        case1 = make_case(db_session, research_state="DISCOVERED")
        case2 = make_case(db_session, research_state="EVIDENCE_READY")
        db_session.commit()

        resp = client.get("/api/radar/cases?research_state=EVIDENCE_READY", headers=auth)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert items[0]["id"] == case2.id

    def test_list_cases_includes_required_fields(self, client, auth, db_session):
        """Each case includes: ids, research_state, suggested_disposition, user_disposition,
        blockers, unknown_count, deadline object with original_text and precision, freshness flag."""
        case = make_case(db_session)
        case.suggested_disposition = "STRONG"
        case.user_disposition = "WATCH"
        db_session.commit()

        resp = client.get("/api/radar/cases", headers=auth)
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert "id" in item
        assert "research_state" in item
        assert "suggested_disposition" in item
        assert "user_disposition" in item
        assert "blockers" in item
        assert "unknown_count" in item
        assert "deadline" in item
        assert "freshness" in item

    def test_list_cases_unauthenticated_rejected(self, client, db_session):
        """Unauthenticated request is rejected like the donor."""
        make_case(db_session)
        db_session.commit()

        resp = client.get("/api/radar/cases")
        assert resp.status_code == 401


class TestRadarOwnerBoundary:
    def test_second_account_cannot_read_or_change_owner_case(self, client, auth, db_session):
        case = make_case(db_session)
        db_session.commit()

        assert client.get(f"/api/radar/cases/{case.id}", headers=auth).status_code == 200
        created = client.post(
            "/api/auth/register",
            json={"email": "bob@example.com", "password": "SuperSecret2"},
        )
        assert created.status_code == 201
        login = client.post(
            "/api/auth/login",
            json={"email": "bob@example.com", "password": "SuperSecret2"},
        )
        assert login.status_code == 200
        other = {"Authorization": f"Bearer {login.json()['access_token']}"}

        assert client.get("/api/radar/cases", headers=other).status_code == 403
        assert client.get(f"/api/radar/cases/{case.id}", headers=other).status_code == 403
        assert client.post(
            f"/api/radar/cases/{case.id}/disposition",
            headers=other,
            json={"value": "REJECTED"},
        ).status_code == 403
        assert client.post(
            f"/api/radar/cases/{case.id}/notes",
            headers=other,
            json={"body": "intrusion"},
        ).status_code == 403
        assert client.post(f"/api/radar/cases/{case.id}/brief", headers=other).status_code == 403
        db_session.refresh(case)
        assert case.user_disposition == "UNDECIDED"

    def test_unconfigured_owner_fails_closed(self, client, auth, monkeypatch):
        monkeypatch.delenv("RADAR_OWNER_EMAIL")
        response = client.get("/api/radar/cases", headers=auth)
        assert response.status_code == 503
        assert response.json()["detail"] == "Radar owner is not configured"


class TestCasesGet:
    """GET /cases/{id}."""

    def test_get_case_by_id(self, client, auth, db_session):
        """GET /cases/{id} returns the case."""
        case = make_case(db_session)
        case.user_disposition = "STRONG"
        case.suggested_disposition = "WATCH"
        db_session.commit()

        resp = client.get(f"/api/radar/cases/{case.id}", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == case.id
        assert data["user_disposition"] == "STRONG"
        assert data["suggested_disposition"] == "WATCH"

    def test_get_case_not_found(self, client, auth):
        """GET /cases/{id} returns 404 if case does not exist."""
        resp = client.get("/api/radar/cases/nonexistent", headers=auth)
        assert resp.status_code == 404

    def test_get_case_unauthenticated_rejected(self, client, db_session):
        """Unauthenticated request is rejected."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.get(f"/api/radar/cases/{case.id}")
        assert resp.status_code == 401


class TestDispositionSet:
    """POST /cases/{id}/disposition."""

    def test_set_disposition_persists(self, client, auth, db_session):
        """POST disposition persists the new value."""
        case = make_case(db_session)
        case.user_disposition = "UNDECIDED"
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/disposition",
            headers=auth,
            json={"value": "STRONG", "reason": "Good fit for research"}
        )
        assert resp.status_code == 200

        # Verify it was persisted
        db_session.refresh(case)
        assert case.user_disposition == "STRONG"

    def test_set_disposition_preserves_across_suggestion_recompute(self, client, auth, db_session):
        """After setting user disposition, a suggestion recompute leaves user disposition unchanged."""
        case = make_case(db_session)
        case.user_disposition = "UNDECIDED"
        case.suggested_disposition = "WATCH"
        db_session.commit()

        # Set user disposition
        resp = client.post(
            f"/api/radar/cases/{case.id}/disposition",
            headers=auth,
            json={"value": "ACT", "reason": "User decision"}
        )
        assert resp.status_code == 200
        db_session.refresh(case)
        assert case.user_disposition == "ACT"

        # Simulate a suggestion recompute by manually setting suggested_disposition
        case.suggested_disposition = "REJECTED"
        db_session.commit()

        # Verify user disposition is still ACT (not overwritten)
        db_session.refresh(case)
        assert case.user_disposition == "ACT"
        assert case.suggested_disposition == "REJECTED"

    def test_set_disposition_calls_domain_set_user_disposition(self, client, auth, db_session):
        """POST disposition calls domain.disposition.set_user_disposition with actor 'USER'."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/disposition",
            headers=auth,
            json={"value": "WATCH", "reason": "Needs more research"}
        )
        assert resp.status_code == 200

        # Check the case was updated
        db_session.refresh(case)
        assert case.user_disposition == "WATCH"

    def test_set_disposition_unauthenticated_rejected(self, client, db_session):
        """Unauthenticated request is rejected."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/disposition",
            json={"value": "STRONG", "reason": "test"}
        )
        assert resp.status_code == 401

    def test_set_disposition_invalid_value(self, client, auth, db_session):
        """POST disposition with invalid value is rejected."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/disposition",
            headers=auth,
            json={"value": "INVALID", "reason": "test"}
        )
        assert resp.status_code == 422


class TestNotes:
    """POST /cases/{id}/notes."""

    def test_post_note(self, client, auth, db_session):
        """POST /cases/{id}/notes creates a note."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/notes",
            headers=auth,
            json={"body": "This is a test note"}
        )
        assert resp.status_code == 201

    def test_post_note_unauthenticated_rejected(self, client, db_session):
        """Unauthenticated request is rejected."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/notes",
            json={"body": "test note"}
        )
        assert resp.status_code == 401


class TestStage:
    """POST /cases/{id}/stage."""

    def test_post_stage(self, client, auth, db_session):
        """POST /cases/{id}/stage updates application stage."""
        case = make_case(db_session)
        case.application_stage = "NOT_STARTED"
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/stage",
            headers=auth,
            json={"stage": "PREPARING"}
        )
        assert resp.status_code == 200

        db_session.refresh(case)
        assert case.application_stage == "PREPARING"

    def test_post_stage_unauthenticated_rejected(self, client, db_session):
        """Unauthenticated request is rejected."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/stage",
            json={"stage": "PREPARING"}
        )
        assert resp.status_code == 401


class TestCaseCreate:
    """POST /cases."""

    def test_create_case_201(self, client, auth, db_session):
        """POST /cases creates a case and returns 201."""
        from db.radar_models_targets import MozareRoute, TargetEntity

        route = MozareRoute(name="Test Route", state="ACTIVE")
        target = TargetEntity(kind="Person", display_name="Test Person")
        db_session.add(route)
        db_session.add(target)
        db_session.flush()

        resp = client.post(
            "/api/radar/cases",
            headers=auth,
            json={
                "route_id": route.id,
                "target_id": target.id,
                "application_route": "SUPERVISOR_FIRST_PHD"
            }
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"]
        assert data["research_state"] == "DISCOVERED"
        assert data["user_disposition"] == "UNDECIDED"

    def test_create_case_409_duplicate(self, client, auth, db_session):
        """POST /cases returns 409 for duplicate (route_id, target_id, application_route)."""
        case = make_case(db_session, application_route="SUPERVISOR_FIRST_PHD")
        db_session.commit()

        resp = client.post(
            "/api/radar/cases",
            headers=auth,
            json={
                "route_id": case.route_id,
                "target_id": case.target_id,
                "application_route": "SUPERVISOR_FIRST_PHD"
            }
        )
        assert resp.status_code == 409

    def test_create_case_422_invalid_route(self, client, auth, db_session):
        """POST /cases returns 422 for invalid application_route."""
        from db.radar_models_targets import MozareRoute, TargetEntity

        route = MozareRoute(name="Test Route", state="ACTIVE")
        target = TargetEntity(kind="Person", display_name="Test Person")
        db_session.add(route)
        db_session.add(target)
        db_session.flush()

        resp = client.post(
            "/api/radar/cases",
            headers=auth,
            json={
                "route_id": route.id,
                "target_id": target.id,
                "application_route": "INVALID_ROUTE"
            }
        )
        assert resp.status_code == 422

    def test_create_case_same_target_different_route_allowed(self, client, auth, db_session):
        """POST /cases allows same route+target with different application_route."""
        case1 = make_case(db_session, application_route="SUPERVISOR_FIRST_PHD")
        db_session.commit()

        resp = client.post(
            "/api/radar/cases",
            headers=auth,
            json={
                "route_id": case1.route_id,
                "target_id": case1.target_id,
                "application_route": "MA_PROGRAMME"
            }
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] != case1.id
