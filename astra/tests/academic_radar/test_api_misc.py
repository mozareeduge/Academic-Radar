"""tests.academic_radar.test_api_misc — Radar misc API endpoints.

Covers GET/POST /funding/{case_id}, GET/POST /watch/targets, GET /watch/changes,
GET/POST /routes, PATCH /routes/{id}, PATCH /routes/{id}/state,
GET/PUT /profile.
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.app import app
from api.deps import get_db
from api.security import login_limiter, register_limiter
from db.models import Base, User
from db.radar_models_cases import EvaluationCase
from db.radar_models_targets import MozareRoute, TargetEntity, CandidateProfile
from db.radar_models_claims import FundingAssessment
from db.radar_models_watch import WatchTarget, ChangeEvent, WatchCheck
from db.radar_models_evidence import SourceSnapshot
from academic_radar.domain.enums import ApplicationRoute, ResearchState, FundingAssessmentState, WatchTargetState, RouteState


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


class TestFundingEndpoint:
    """GET /funding/{case_id} and POST /funding/{case_id}."""

    def test_get_funding_empty_list(self, client, auth, db_session):
        """GET /funding/{case_id} with no funding returns empty list."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.get(f"/api/radar/funding/{case.id}", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_funding_amounts_are_strings_not_floats(self, client, auth, db_session):
        """Funding response amounts are strings, never floats, to preserve Decimal precision."""
        funding_route = TargetEntity(kind="FundingRoute", display_name="Test Funding")
        session = db_session
        session.add(funding_route)
        session.flush()

        case = make_case(db_session)
        db_session.commit()

        # Add funding assessment with Decimal amounts
        funding = FundingAssessment(
            case_id=case.id,
            funding_route_id=funding_route.id,
            currency="GBP",
            award_amount=Decimal("25000.50"),
            tuition_amount=Decimal("9250.75"),
            duration_months=12,
            state=FundingAssessmentState.FUNDING_GAP,
        )
        session.add(funding)
        session.commit()

        resp = client.get(f"/api/radar/funding/{case.id}", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        item = data["items"][0]

        # Verify amounts are strings, not floats
        assert isinstance(item["award_amount"], str), "award_amount should be string"
        assert isinstance(item["tuition_amount"], str), "tuition_amount should be string"
        assert item["award_amount"] == "25000.50"
        assert item["tuition_amount"] == "9250.75"

    # ORACLE-007
    def test_post_funding_creates_assessment(self, client, auth, db_session):
        """POST /funding/{case_id} creates a new FundingAssessment."""
        funding_route = TargetEntity(kind="FundingRoute", display_name="Test Funding")
        session = db_session
        session.add(funding_route)
        session.flush()

        case = make_case(db_session)
        db_session.commit()

        payload = {
            "funding_route_id": funding_route.id,
            "currency": "GBP",
            "award_amount": "15000",
            "tuition_amount": "9250",
            "duration_months": 12,
            "state": "ELIGIBLE"
        }
        resp = client.post(f"/api/radar/funding/{case.id}", json=payload, headers=auth)
        assert resp.status_code == 201
        data = resp.json()
        assert data["currency"] == "GBP"
        assert data["award_amount"] == "15000.00"

    def test_funding_case_not_found(self, client, auth):
        """GET /funding/{case_id} with non-existent case returns 404."""
        resp = client.get("/api/radar/funding/nonexistent", headers=auth)
        assert resp.status_code == 404


class TestWatchEndpoints:
    """GET/POST /watch/targets and GET /watch/changes."""

    def test_get_watch_targets_empty(self, client, auth, db_session):
        """GET /watch/targets returns empty list."""
        db_session.commit()
        resp = client.get("/api/radar/watch/targets", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_get_watch_targets_lists_all(self, client, auth, db_session):
        """GET /watch/targets returns all watch targets."""
        target = TargetEntity(kind="Person", display_name="Watched Person")
        session = db_session
        session.add(target)
        session.flush()

        watch = WatchTarget(
            target_id=target.id,
            url="https://example.com",
            cadence="weekly",
            state="ACTIVE"
        )
        session.add(watch)
        session.commit()

        resp = client.get("/api/radar/watch/targets", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["url"] == "https://example.com"

    def test_post_watch_target_creates(self, client, auth, db_session):
        """POST /watch/targets creates a new watch target."""
        target = TargetEntity(kind="Person", display_name="Test Person")
        session = db_session
        session.add(target)
        session.flush()
        db_session.commit()

        payload = {
            "target_id": target.id,
            "url": "https://example.com/person",
            "cadence": "daily",
            "state": "ACTIVE"
        }
        resp = client.post("/api/radar/watch/targets", json=payload, headers=auth)
        assert resp.status_code == 201
        data = resp.json()
        assert data["url"] == "https://example.com/person"

    def test_get_watch_changes_lists_events_with_impacted_cases(self, client, auth, db_session):
        """GET /watch/changes returns events with impacted cases via invalidation report."""
        # Create target, watch, and a change event
        target = TargetEntity(kind="Person", display_name="Person")
        session = db_session
        session.add(target)
        session.flush()

        watch = WatchTarget(
            target_id=target.id,
            url="https://example.com",
            cadence="weekly",
            state="ACTIVE"
        )
        session.add(watch)
        session.flush()

        # Create a snapshot (mimicking a watch check fetch)
        from datetime import datetime, timezone
        snapshot = SourceSnapshot(
            source_url="https://example.com",
            state="CHANGED",
            captured_at=datetime.now(timezone.utc)
        )
        session.add(snapshot)
        session.flush()

        # Create watch check
        check = WatchCheck(
            watch_target_id=watch.id,
            snapshot_id=snapshot.id,
            changed=True
        )
        session.add(check)
        session.flush()

        # Create change event
        change_event = ChangeEvent(
            watch_check_id=check.id,
            summary="Content updated",
            material=True
        )
        session.add(change_event)
        session.commit()

        resp = client.get("/api/radar/watch/changes", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) >= 1
        # Change events should have impacted_cases field (even if empty when no invalidation)
        assert "impacted_cases" in data["items"][0]


class TestRoutesEndpoints:
    """GET /routes and PATCH /routes/{id}/state."""

    def test_get_routes_lists_all(self, client, auth, db_session):
        """GET /routes returns all routes."""
        route1 = MozareRoute(name="Route One", state="ACTIVE")
        route2 = MozareRoute(name="Route Two", state="EXPLORATORY")
        session = db_session
        session.add(route1)
        session.add(route2)
        session.commit()

        resp = client.get("/api/radar/routes", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2

    def test_patch_route_state_updates(self, client, auth, db_session):
        """PATCH /routes/{id}/state updates route state."""
        route = MozareRoute(name="Test Route", state="ACTIVE")
        session = db_session
        session.add(route)
        session.commit()

        payload = {"state": "DORMANT"}
        resp = client.patch(f"/api/radar/routes/{route.id}/state", json=payload, headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "DORMANT"

    def test_patch_route_state_validates_against_enum(self, client, auth, db_session):
        """PATCH /routes/{id}/state validates state against RouteState enum."""
        route = MozareRoute(name="Test Route", state="ACTIVE")
        session = db_session
        session.add(route)
        session.commit()

        payload = {"state": "INVALID_STATE"}
        resp = client.patch(f"/api/radar/routes/{route.id}/state", json=payload, headers=auth)
        assert resp.status_code == 422

    def test_patch_route_state_not_found(self, client, auth):
        """PATCH /routes/{id}/state with non-existent route returns 404."""
        payload = {"state": "RETIRED"}
        resp = client.patch("/api/radar/routes/nonexistent/state", json=payload, headers=auth)
        assert resp.status_code == 404

    def test_post_routes_creates_a_route(self, client, auth):
        """POST /routes creates a new MozareRoute with the submitted fields."""
        payload = {
            "name": "Quantum Simulation Route",
            "state": "ACTIVE",
            "route_statement": "Investigate quantum simulation supervisors.",
            "core_problem": "Decoherence limits practical quantum advantage.",
            "operations_methods": ["Topological error correction", "Tensor networks"],
            "relevant_corpora_material": ["arXiv quant-ph"],
            "target_disciplines": ["Quantum Physics"],
            "prohibited_overclaims": ["Claims of near-term quantum advantage"],
            "maturity": "EXPLORATORY",
        }
        resp = client.post("/api/radar/routes", json=payload, headers=auth)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Quantum Simulation Route"
        assert data["state"] == "ACTIVE"
        assert data["operations_methods"] == payload["operations_methods"]
        assert data["target_disciplines"] == payload["target_disciplines"]
        assert data["maturity"] == "EXPLORATORY"

        listed = client.get("/api/radar/routes", headers=auth)
        assert len(listed.json()["items"]) == 1

    def test_post_routes_validates_state_enum(self, client, auth):
        """POST /routes rejects a state outside the RouteState enum."""
        resp = client.post(
            "/api/radar/routes",
            json={"name": "Bad Route", "state": "NOT_A_STATE"},
            headers=auth,
        )
        assert resp.status_code == 422

    def test_patch_route_updates_fields(self, client, auth, db_session):
        """PATCH /routes/{id} edits route fields without touching state via this path."""
        route = MozareRoute(name="Original Name", state="ACTIVE", maturity="EXPLORATORY")
        session = db_session
        session.add(route)
        session.commit()

        resp = client.patch(
            f"/api/radar/routes/{route.id}",
            json={
                "name": "Renamed Route",
                "core_problem": "Updated problem statement",
                "operations_methods": ["New method"],
            },
            headers=auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Renamed Route"
        assert data["core_problem"] == "Updated problem statement"
        assert data["operations_methods"] == ["New method"]
        # Fields not sent in the PATCH body are left unchanged.
        assert data["maturity"] == "EXPLORATORY"
        assert data["state"] == "ACTIVE"

    def test_patch_route_can_deactivate_via_state(self, client, auth, db_session):
        """PATCH /routes/{id} can also retire a route in the same save."""
        route = MozareRoute(name="Test Route", state="ACTIVE")
        session = db_session
        session.add(route)
        session.commit()

        resp = client.patch(
            f"/api/radar/routes/{route.id}",
            json={"state": "RETIRED"},
            headers=auth,
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "RETIRED"

    def test_patch_route_validates_state_enum(self, client, auth, db_session):
        """PATCH /routes/{id} rejects an invalid state value."""
        route = MozareRoute(name="Test Route", state="ACTIVE")
        session = db_session
        session.add(route)
        session.commit()

        resp = client.patch(
            f"/api/radar/routes/{route.id}",
            json={"state": "NOT_A_STATE"},
            headers=auth,
        )
        assert resp.status_code == 422

    def test_patch_route_not_found(self, client, auth):
        """PATCH /routes/{id} with an unknown id returns 404."""
        resp = client.patch(
            "/api/radar/routes/nonexistent",
            json={"name": "Whatever"},
            headers=auth,
        )
        assert resp.status_code == 404


class TestProfileEndpoint:
    """GET /profile and PUT /profile."""

    def test_get_profile_returns_current_candidate_profile(self, client, auth, db_session):
        """GET /profile returns the active CandidateProfile."""
        profile = CandidateProfile(
            state="ACTIVE",
            education={"degree": "MA Philosophy"},
        )
        session = db_session
        session.add(profile)
        session.commit()

        resp = client.get("/api/radar/profile", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "ACTIVE"

    def test_get_profile_not_found(self, client, auth, db_session):
        """GET /profile with no profile returns 404."""
        db_session.commit()
        resp = client.get("/api/radar/profile", headers=auth)
        assert resp.status_code == 404

    def test_put_profile_creates_when_none_exists(self, client, auth, db_session):
        """PUT /profile creates the ACTIVE profile on first save."""
        db_session.commit()

        payload = {
            "fixed_constraints": "English language proficiency (IELTS 7.0+)",
            "education": [
                {"degree": "BSc Physics", "institution": "University of Example", "year": 2020},
            ],
        }
        resp = client.put("/api/radar/profile", json=payload, headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "ACTIVE"
        assert data["fixed_constraints"] == payload["fixed_constraints"]
        assert data["education"] == [
            {
                "degree": "BSc Physics",
                "institution": "University of Example",
                "year": 2020,
                "provenance": {
                    "source": "Self-reported via profile form",
                    "verified": False,
                },
            },
        ]

        # GET reflects the same profile, and there is exactly one row.
        listed = client.get("/api/radar/profile", headers=auth)
        assert listed.status_code == 200
        assert listed.json()["id"] == data["id"]
        assert db_session.query(CandidateProfile).count() == 1

    def test_put_profile_updates_existing_active_profile(self, client, auth, db_session):
        """PUT /profile updates the existing ACTIVE row rather than creating a second one."""
        profile = CandidateProfile(state="ACTIVE", fixed_constraints="Old constraint")
        session = db_session
        session.add(profile)
        session.commit()
        profile_id = profile.id

        resp = client.put(
            "/api/radar/profile",
            json={"fixed_constraints": "New constraint"},
            headers=auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == profile_id
        assert data["fixed_constraints"] == "New constraint"
        assert db_session.query(CandidateProfile).count() == 1

    def test_put_profile_strips_client_provenance_and_defaults_it(self, client, auth, db_session):
        """A client cannot mark its own facts as independently verified."""
        db_session.commit()

        resp = client.put(
            "/api/radar/profile",
            json={
                "scholarly_work": [
                    {
                        "title": "A paper",
                        "provenance": {"source": "Fabricated", "verified": True},
                    },
                ],
            },
            headers=auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["scholarly_work"] == [
            {
                "title": "A paper",
                "provenance": {
                    "source": "Self-reported via profile form",
                    "verified": False,
                },
            },
        ]

    def test_put_profile_omitted_section_is_left_unchanged(self, client, auth, db_session):
        """Sections not present in the request body are left as-is."""
        profile = CandidateProfile(
            state="ACTIVE",
            language_evidence=[
                {
                    "language": "English",
                    "proficiency_level": "C1",
                    "provenance": {"source": "IELTS certificate", "verified": True},
                },
            ],
        )
        session = db_session
        session.add(profile)
        session.commit()

        resp = client.put(
            "/api/radar/profile",
            json={"fixed_constraints": "Updated only this"},
            headers=auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fixed_constraints"] == "Updated only this"
        assert data["language_evidence"][0]["language"] == "English"
        assert data["language_evidence"][0]["provenance"]["verified"] is True

    def test_put_profile_rejects_non_object_fact(self, client, auth, db_session):
        """A fact list item that isn't an object is a 422, not a silent drop."""
        db_session.commit()

        resp = client.put(
            "/api/radar/profile",
            json={"education": ["not an object"]},
            headers=auth,
        )
        assert resp.status_code == 422
