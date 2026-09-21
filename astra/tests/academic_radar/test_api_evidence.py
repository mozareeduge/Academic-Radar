"""tests.academic_radar.test_api_evidence — Evidence inspector, research runs, coverage.

Covers:
- GET /claims/{id}/evidence: evidence artifacts with source_url, authority, retrieved_at, excerpt, independent_support_count, contradiction state
- GET /cases/{id}/coverage: per evidence class CoverageStatus + evidence ids + protocol version
- POST /cases/{id}/research: enqueues research job with generated run_key; returns run id
- GET /runs/{id}: status, failure reason, run identity without secrets
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from api.app import app
from api.deps import get_db
from api.security import login_limiter, register_limiter
from db.models import Base, User
from db.radar_models_cases import EvaluationCase
from db.radar_models_evidence import EvidenceArtifact, ResearchRun, ResearchCoverage, SourceSnapshot
from db.radar_models_claims import Claim, ClaimEvidence
from db.repositories import UserRepo
from academic_radar.domain.enums import ApplicationRoute, ResearchState


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


class TestEvidenceGet:
    """GET /claims/{id}/evidence."""

    def test_evidence_returns_source_url_authority_retrieved_excerpt(self, client, auth, db_session):
        """Evidence endpoint returns source_url, authority, retrieved_at, excerpt."""
        snapshot = SourceSnapshot(
            source_url="https://example.com/page",
            state="CAPTURED",
            captured_at=datetime.now(timezone.utc)
        )
        db_session.add(snapshot)
        db_session.flush()

        artifact = EvidenceArtifact(
            source_url="https://example.com/page",
            source_type="webpage",
            excerpt="This is evidence text.",
            snapshot_id=snapshot.id,
            retrieved_at=datetime.now(timezone.utc),
            source_authority="OFFICIAL_PROGRAMME"
        )
        db_session.add(artifact)
        db_session.flush()

        case = make_case(db_session)
        db_session.commit()

        claim = Claim(
            case_id=case.id,
            statement="Test claim",
            claim_type="EXTERNAL_FACT",
            status="SUPPORTED"
        )
        db_session.add(claim)
        db_session.flush()

        # Link claim to artifact
        link = ClaimEvidence(
            claim_id=claim.id,
            evidence_artifact_id=artifact.id
        )
        db_session.add(link)
        db_session.commit()

        resp = client.get(f"/api/radar/claims/{claim.id}/evidence", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["artifacts"]) == 1
        art = data["artifacts"][0]
        assert art["source_url"] == "https://example.com/page"
        assert art["authority"] == "OFFICIAL_PROGRAMME"
        assert "retrieved_at" in art
        assert art["excerpt"] == "This is evidence text."

    def test_evidence_returns_independent_support_count(self, client, auth, db_session):
        """Evidence endpoint returns independent_support_count."""
        snapshot = SourceSnapshot(
            source_url="https://example.com",
            state="CAPTURED",
            captured_at=datetime.now(timezone.utc)
        )
        db_session.add(snapshot)
        db_session.flush()

        artifact1 = EvidenceArtifact(
            source_url="https://example.com/page1",
            source_authority="AUTHORITATIVE_REGISTRY",
            excerpt="First source",
            retrieved_at=datetime.now(timezone.utc),
            snapshot_id=snapshot.id
        )
        artifact2 = EvidenceArtifact(
            source_url="https://different.com/page",
            source_authority="OFFICIAL_DEPARTMENT_OR_PERSON",
            excerpt="Second source",
            retrieved_at=datetime.now(timezone.utc),
            snapshot_id=snapshot.id,
            canonical_origin="different_origin"
        )
        db_session.add(artifact1)
        db_session.add(artifact2)
        db_session.flush()

        case = make_case(db_session)
        db_session.commit()

        claim = Claim(
            case_id=case.id,
            statement="Test claim",
            claim_type="EXTERNAL_FACT",
            status="SUPPORTED"
        )
        db_session.add(claim)
        db_session.flush()

        link1 = ClaimEvidence(
            claim_id=claim.id,
            evidence_artifact_id=artifact1.id
        )
        link2 = ClaimEvidence(
            claim_id=claim.id,
            evidence_artifact_id=artifact2.id
        )
        db_session.add(link1)
        db_session.add(link2)
        db_session.commit()

        resp = client.get(f"/api/radar/claims/{claim.id}/evidence", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["independent_support_count"] == 2

    def test_evidence_contradiction_state(self, client, auth, db_session):
        """Evidence endpoint returns contradiction state from claim status."""
        snapshot = SourceSnapshot(
            source_url="https://example.com",
            state="CAPTURED",
            captured_at=datetime.now(timezone.utc)
        )
        db_session.add(snapshot)
        db_session.flush()

        artifact = EvidenceArtifact(
            source_url="https://example.com/page",
            source_authority="OFFICIAL_PROGRAMME",
            excerpt="Contradictory info",
            retrieved_at=datetime.now(timezone.utc),
            snapshot_id=snapshot.id
        )
        db_session.add(artifact)
        db_session.flush()

        case = make_case(db_session)
        db_session.commit()

        claim = Claim(
            case_id=case.id,
            statement="Contradicted claim",
            claim_type="EXTERNAL_FACT",
            status="CONTRADICTED"
        )
        db_session.add(claim)
        db_session.flush()

        link = ClaimEvidence(
            claim_id=claim.id,
            evidence_artifact_id=artifact.id
        )
        db_session.add(link)
        db_session.commit()

        resp = client.get(f"/api/radar/claims/{claim.id}/evidence", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["contradiction_state"] == "CONTRADICTED"


class TestCoverageCases:
    """GET /cases/{id}/coverage."""

    def test_coverage_returns_all_four_statuses_distinctly(self, client, auth, db_session):
        """Coverage endpoint shows all four CoverageStatus values distinctly."""
        case = make_case(db_session)
        db_session.commit()

        # Create a research run
        run = ResearchRun(
            case_id=case.id,
            protocol_version="1.0",
            status="COMPLETED"
        )
        db_session.add(run)
        db_session.flush()

        # Create coverage records for each status
        cov1 = ResearchCoverage(
            run_id=run.id,
            evidence_class="supervisor_publications",
            status="SEARCHED_FOUND",
            evidence_ids=["evt1", "evt2"]
        )
        cov2 = ResearchCoverage(
            run_id=run.id,
            evidence_class="student_prior_formation",
            status="SEARCHED_NONE_FOUND",
            evidence_ids=[]
        )
        cov3 = ResearchCoverage(
            run_id=run.id,
            evidence_class="funding_evidence",
            status="NOT_SEARCHED",
            evidence_ids=[]
        )
        cov4 = ResearchCoverage(
            run_id=run.id,
            evidence_class="blocked_evidence",
            status="BLOCKED",
            evidence_ids=[]
        )
        db_session.add_all([cov1, cov2, cov3, cov4])
        db_session.commit()

        resp = client.get(f"/api/radar/cases/{case.id}/coverage", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert "coverage" in data
        statuses = {c["evidence_class"]: c["status"] for c in data["coverage"]}
        assert statuses["supervisor_publications"] == "SEARCHED_FOUND"
        assert statuses["student_prior_formation"] == "SEARCHED_NONE_FOUND"
        assert statuses["funding_evidence"] == "NOT_SEARCHED"
        assert statuses["blocked_evidence"] == "BLOCKED"

    def test_coverage_includes_evidence_ids(self, client, auth, db_session):
        """Coverage endpoint includes evidence_ids array for each class."""
        case = make_case(db_session)
        db_session.commit()

        run = ResearchRun(
            case_id=case.id,
            protocol_version="1.0",
            status="COMPLETED"
        )
        db_session.add(run)
        db_session.flush()

        cov = ResearchCoverage(
            run_id=run.id,
            evidence_class="supervisor_publications",
            status="SEARCHED_FOUND",
            evidence_ids=["id1", "id2", "id3"]
        )
        db_session.add(cov)
        db_session.commit()

        resp = client.get(f"/api/radar/cases/{case.id}/coverage", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        found = [c for c in data["coverage"] if c["evidence_class"] == "supervisor_publications"][0]
        assert found["evidence_ids"] == ["id1", "id2", "id3"]

    def test_coverage_includes_protocol_version(self, client, auth, db_session):
        """Coverage endpoint includes protocol_version from the run."""
        case = make_case(db_session)
        db_session.commit()

        run = ResearchRun(
            case_id=case.id,
            protocol_version="2.5.1",
            status="COMPLETED"
        )
        db_session.add(run)
        db_session.flush()

        cov = ResearchCoverage(
            run_id=run.id,
            evidence_class="test_class",
            status="SEARCHED_FOUND",
            evidence_ids=[]
        )
        db_session.add(cov)
        db_session.commit()

        resp = client.get(f"/api/radar/cases/{case.id}/coverage", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["protocol_version"] == "2.5.1"


class TestResearchPost:
    """POST /cases/{id}/research."""

    @pytest.fixture(autouse=True)
    def configured_queue(self, monkeypatch):
        from api.routes import radar_evidence
        queue = MagicMock()
        queue.enqueue.return_value.id = "job-1"
        monkeypatch.setattr(radar_evidence, "provider_config", lambda: {"provider_id": "litellm", "model_id": "test/model"})
        monkeypatch.setattr(radar_evidence, "research_queue", lambda: queue)
        self.queue = queue

    def test_research_enqueues_job_and_returns_run_id(self, client, auth, db_session):
        """POST /cases/{id}/research enqueues research job and returns run id."""
        case = make_case(db_session)
        db_session.commit()

        resp = client.post(
            f"/api/radar/cases/{case.id}/research",
            headers=auth,
            json={}
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "run_id" in data
        run_id = data["run_id"]

        # Verify the run was created
        run = db_session.query(ResearchRun).filter(ResearchRun.id == run_id).first()
        assert run is not None
        assert run.case_id == case.id
        assert run.status == "QUEUED"
        assert run.model_id == "test/model"
        assert run.provider_id == "litellm"
        args, kwargs = self.queue.enqueue.call_args
        assert args[1:3] == (case.id, run.id)
        assert kwargs["kwargs"]["deps"]["run_id"] == run.id

    def test_research_post_twice_same_key_does_not_enqueue_twice(self, client, auth, db_session):
        """POST research twice with same key does not enqueue twice."""
        case = make_case(db_session)
        db_session.commit()

        # First POST
        resp1 = client.post(
            f"/api/radar/cases/{case.id}/research",
            headers=auth,
            json={"run_key": "my-key"}
        )
        assert resp1.status_code == 202
        run_id_1 = resp1.json()["run_id"]

        # Second POST with same key
        resp2 = client.post(
            f"/api/radar/cases/{case.id}/research",
            headers=auth,
            json={"run_key": "my-key"}
        )
        assert resp2.status_code == 202
        run_id_2 = resp2.json()["run_id"]

        # Should be the same run (idempotent)
        assert run_id_1 == run_id_2
        assert self.queue.enqueue.call_count == 1

    def test_queue_failure_marks_run_failed(self, client, auth, db_session, monkeypatch):
        case = make_case(db_session)
        db_session.commit()
        self.queue.enqueue.side_effect = ConnectionError("redis down")

        resp = client.post(f"/api/radar/cases/{case.id}/research", headers=auth, json={})
        assert resp.status_code == 503
        run = db_session.query(ResearchRun).filter_by(case_id=case.id).one()
        assert run.status == "FAILED"
        assert run.run_identity["failure_reason"] == "QUEUE_UNAVAILABLE"

    def test_missing_provider_config_creates_no_run(self, client, auth, db_session, monkeypatch):
        from api.routes import radar_evidence
        case = make_case(db_session)
        db_session.commit()
        monkeypatch.setattr(radar_evidence, "provider_config", lambda: (_ for _ in ()).throw(ValueError("unconfigured")))

        resp = client.post(f"/api/radar/cases/{case.id}/research", headers=auth, json={})
        assert resp.status_code == 503
        assert db_session.query(ResearchRun).filter_by(case_id=case.id).count() == 0


class TestRunsGet:
    """GET /runs/{id}."""

    def test_run_returns_status_and_failure_reason(self, client, auth, db_session):
        """GET /runs/{id} returns status and failure_reason."""
        case = make_case(db_session)
        db_session.commit()

        run = ResearchRun(
            case_id=case.id,
            protocol_version="1.0",
            status="FAILED"
        )
        db_session.add(run)
        db_session.commit()

        resp = client.get(f"/api/radar/runs/{run.id}", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "FAILED"
        assert "failure_reason" in data

    def test_run_identity_contains_no_secrets(self, client, auth, db_session):
        """GET /runs/{id} run identity response contains no key/secret patterns."""
        case = make_case(db_session)
        db_session.commit()

        run = ResearchRun(
            case_id=case.id,
            protocol_version="1.0",
            status="COMPLETED",
            model_id="gpt-4",
            provider_id="openai"
        )
        db_session.add(run)
        db_session.flush()

        run.run_identity = {
            "model_id": "gpt-4",
            "provider_id": "openai",
            "prompt_hash": "abc123def456",
            "schema_version": "1.0",
            "protocol_version": "1.0",
            "run_id": run.id
        }
        db_session.commit()

        resp = client.get(f"/api/radar/runs/{run.id}", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        response_text = str(data)

        # Check for common secret patterns using redact module patterns
        assert "sk-" not in response_text  # OpenAI API key pattern
        assert "Bearer" not in response_text or "[REDACTED]" in response_text
        assert "api_key=" not in response_text or "[REDACTED]" in response_text
