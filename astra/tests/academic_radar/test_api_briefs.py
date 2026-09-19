"""tests.academic_radar.test_api_briefs — Radar application brief API endpoints.

Covers POST /api/radar/cases/{id}/brief (freeze brief) and
GET /api/radar/briefs/{id} (retrieve brief with superseded flag).

SCN-036: Generate Application Brief
SCN-037: Case changes after brief → superseded flag
SCN-012: Stale critical facts block brief freeze (409 Conflict)
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.app import app
from api.deps import get_db
from api.security import login_limiter, register_limiter
from db.models import Base, User
from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import Claim, GateAssessment, ClaimEvidence
from db.radar_models_evidence import EvidenceArtifact, SourceSnapshot
from db.radar_models_watch import ApplicationBrief, BriefDependency
from db.repositories import UserRepo
from academic_radar.domain.enums import ApplicationRoute, ResearchState, GateResult, ClaimStatus


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
    import db.radar_models_targets  # noqa: F401
    import db.radar_models_cases  # noqa: F401
    import db.radar_models_evidence  # noqa: F401
    import db.radar_models_claims  # noqa: F401
    import db.radar_models_watch  # noqa: F401

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


def make_case_with_evidence(session, case_id: str = "test-case") -> dict:
    """Create a case with claims, gates, and fresh evidence."""
    from db.radar_models_targets import MozareRoute, TargetEntity

    now = datetime.now(timezone.utc)

    route = MozareRoute(name="Test Route", state="ACTIVE")
    session.add(route)
    session.flush()

    target = TargetEntity(kind="Person", display_name="Test Person")
    session.add(target)
    session.flush()

    case = EvaluationCase(
        id=case_id,
        route_id=route.id,
        target_id=target.id,
        application_route="SUPERVISOR_FIRST_PHD",
        research_state="EVIDENCE_READY"
    )
    session.add(case)
    session.flush()

    snapshot = SourceSnapshot(
        source_url="https://example.com",
        state="CAPTURED",
        fingerprint="abc123",
        captured_at=now,
    )
    session.add(snapshot)
    session.flush()

    artifact = EvidenceArtifact(
        source_url="https://example.com",
        source_type="OFFICIAL_PROGRAMME",
        snapshot_id=snapshot.id,
        retrieved_at=now,
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.flush()

    claim = Claim(
        case_id=case.id,
        statement="Test claim",
        claim_type="EXTERNAL_FACT",
        status=ClaimStatus.SUPPORTED.value,
    )
    session.add(claim)
    session.flush()

    ce = ClaimEvidence(
        claim_id=claim.id,
        evidence_artifact_id=artifact.id,
    )
    session.add(ce)

    gate = GateAssessment(
        case_id=case.id,
        requirement="Test requirement",
        source_authority="OFFICIAL_PROGRAMME",
        result=GateResult.PASS.value,
    )
    session.add(gate)

    session.commit()

    return {
        "case_id": case.id,
        "snapshot_id": snapshot.id,
        "artifact_id": artifact.id,
    }


class TestFreezeBriefEndpoint:
    """POST /api/radar/cases/{id}/brief endpoint."""

    def test_freeze_brief_success(self, client, auth, db_session):
        """Freeze brief returns 200 with brief id and metadata."""
        setup = make_case_with_evidence(db_session, "case-freeze-success")

        resp = client.post(
            f"/api/radar/cases/{setup['case_id']}/brief",
            headers=auth
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["case_id"] == setup["case_id"]
        assert data["state"] == "DRAFT"
        assert "frozen_at" in data

    def test_freeze_brief_returns_409_with_reasons_header(self, client, auth, db_session):
        """Freeze returns 409 Conflict with blocked reasons when brief cannot be frozen."""
        from db.radar_models_targets import MozareRoute, TargetEntity

        route = MozareRoute(name="Test Route", state="ACTIVE")
        db_session.add(route)
        db_session.flush()

        target = TargetEntity(kind="Person", display_name="Test Person")
        db_session.add(target)
        db_session.flush()

        case = EvaluationCase(
            id="case-blocked",
            route_id=route.id,
            target_id=target.id,
            application_route="MA_PROGRAMME",
            research_state="EVIDENCE_READY"
        )
        db_session.add(case)
        db_session.flush()

        gate = GateAssessment(
            case_id=case.id,
            requirement="Formal eligibility",
            source_authority="OFFICIAL_PROGRAMME",
            result=GateResult.UNKNOWN.value,
        )
        db_session.add(gate)
        db_session.commit()

        resp = client.post(
            "/api/radar/cases/case-blocked/brief",
            headers=auth
        )
        assert resp.status_code == 409
        data = resp.json()
        assert "brief" in data["detail"].lower() or "stale" in data["detail"].lower() or "unknown" in data["detail"].lower()

    def test_freeze_brief_blocked_unknown_hard_gate(self, client, auth, db_session):
        """Freeze returns 409 when hard gate is UNKNOWN."""
        from db.radar_models_targets import MozareRoute, TargetEntity

        now = datetime.now(timezone.utc)

        route = MozareRoute(name="Test Route", state="ACTIVE")
        db_session.add(route)
        db_session.flush()

        target = TargetEntity(kind="Person", display_name="Test Person")
        db_session.add(target)
        db_session.flush()

        case = EvaluationCase(
            id="case-unknown-gate",
            route_id=route.id,
            target_id=target.id,
            application_route="SUPERVISOR_FIRST_PHD",
            research_state="EVIDENCE_READY"
        )
        db_session.add(case)
        db_session.flush()

        gate = GateAssessment(
            case_id=case.id,
            requirement="Hard gate",
            source_authority="OFFICIAL_PROGRAMME",
            result=GateResult.UNKNOWN.value,
        )
        db_session.add(gate)
        db_session.commit()

        resp = client.post(
            "/api/radar/cases/case-unknown-gate/brief",
            headers=auth
        )
        assert resp.status_code == 409
        assert "unknown" in resp.json()["detail"].lower() or "hard" in resp.json()["detail"].lower()

    def test_freeze_brief_case_not_found(self, client, auth):
        """Freeze returns 404 when case not found."""
        resp = client.post(
            "/api/radar/cases/nonexistent-case/brief",
            headers=auth
        )
        assert resp.status_code == 404

    def test_freeze_brief_records_dependencies(self, client, auth, db_session):
        """Frozen brief records snapshot dependencies."""
        setup = make_case_with_evidence(db_session, "case-deps")

        resp = client.post(
            f"/api/radar/cases/{setup['case_id']}/brief",
            headers=auth
        )
        assert resp.status_code == 200
        brief_id = resp.json()["id"]

        deps = db_session.query(BriefDependency).filter(
            BriefDependency.brief_id == brief_id
        ).all()
        assert len(deps) > 0


class TestGetBriefEndpoint:
    """GET /api/radar/briefs/{id} endpoint."""

    def test_get_brief_success(self, client, auth, db_session):
        """Get brief returns 200 with correct structure."""
        setup = make_case_with_evidence(db_session, "case-get")

        freeze_resp = client.post(
            f"/api/radar/cases/{setup['case_id']}/brief",
            headers=auth
        )
        brief_id = freeze_resp.json()["id"]

        resp = client.get(
            f"/api/radar/briefs/{brief_id}",
            headers=auth
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == brief_id
        assert data["case_id"] == setup["case_id"]
        assert data["state"] == "DRAFT"
        assert "superseded" in data

    def test_get_brief_not_found(self, client, auth):
        """Get brief returns 404 when not found."""
        resp = client.get(
            "/api/radar/briefs/nonexistent-brief",
            headers=auth
        )
        assert resp.status_code == 404

    def test_brief_not_superseded_when_fresh(self, client, auth, db_session):
        """Brief is not superseded when snapshot unchanged."""
        setup = make_case_with_evidence(db_session, "case-fresh")

        freeze_resp = client.post(
            f"/api/radar/cases/{setup['case_id']}/brief",
            headers=auth
        )
        brief_id = freeze_resp.json()["id"]

        resp = client.get(
            f"/api/radar/briefs/{brief_id}",
            headers=auth
        )
        assert resp.status_code == 200
        assert resp.json()["superseded"] is False

    def test_brief_superseded_when_snapshot_changed(self, client, auth, db_session):
        """Brief becomes superseded when snapshot fingerprint changes."""
        setup = make_case_with_evidence(db_session, "case-change")

        freeze_resp = client.post(
            f"/api/radar/cases/{setup['case_id']}/brief",
            headers=auth
        )
        brief_id = freeze_resp.json()["id"]

        db_session.execute(
            text("UPDATE radar_source_snapshots SET fingerprint = :new_fp WHERE id = :id"),
            {"new_fp": "changed-hash", "id": setup["snapshot_id"]}
        )
        db_session.commit()

        resp = client.get(
            f"/api/radar/briefs/{brief_id}",
            headers=auth
        )
        assert resp.status_code == 200
        assert resp.json()["superseded"] is True
