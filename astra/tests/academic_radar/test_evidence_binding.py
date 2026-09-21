"""Tests for case-scoped evidence acquisition and binding.

The live-provider fail-closed contract: research on a case with no acquirable
case-scoped evidence must raise before any provider is resolved, and a
successful acquisition must bind append-only snapshots + artifacts the same
way watch and fixture evidence do.
"""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from academic_radar.evidence.binding import (
    acquire_case_evidence,
    bind_or_fail,
    case_source_urls,
)
from db.radar_models_cases import EvaluationCase
from db.radar_models_evidence import EvidenceArtifact, SourceSnapshot
from db.radar_models_targets import Programme


def make_temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    normalized_path = path.replace("\\", "/")
    return f"sqlite:///{normalized_path}", path


@pytest.fixture
def db_session():
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
        engine = create_engine(db_url)
        with Session(engine) as session:
            yield session
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


class FakeResult:
    def __init__(self, url=None, status=200, content_type="text/html", body=b"<html>Programme page</html>", error=None):
        self.url = url
        self.status_code = status
        self.content_type = content_type
        self.body_bytes = body
        self.error = error


def _seed_ma_case(session, *, target_id="target-e1", case_id="case-e1",
                  canonical_url="https://example.com/programme"):
    now = datetime.now(timezone.utc)
    session.execute(text(
        "INSERT INTO radar_mozare_routes (id, name, state, created_at, updated_at)"
        " VALUES ('route-e1', 'MA Programme', 'ACTIVE', :n, :n)"
    ), {"n": now})
    session.execute(text(
        "INSERT INTO radar_target_entities (id, kind, display_name, canonical_url, created_at, updated_at)"
        " VALUES (:tid, 'Programme', 'Test Programme', :url, :n, :n)"
    ), {"tid": target_id, "url": canonical_url, "n": now})
    session.execute(text(
        "INSERT INTO radar_programmes (id, target_entity_id, display_name, created_at, updated_at)"
        " VALUES ('prog-e1', :tid, 'Test Programme', :n, :n)"
    ), {"tid": target_id, "n": now})
    session.execute(text(
        "INSERT INTO radar_evaluation_cases (id, route_id, target_id, application_route,"
        " research_state, user_disposition, application_stage, created_at, updated_at)"
        " VALUES (:cid, 'route-e1', :tid, 'MA_PROGRAMME', 'EVIDENCE_READY', 'ACT',"
        " 'APPLICATION_OPEN', :n, :n)"
    ), {"cid": case_id, "tid": target_id, "n": now})
    session.commit()
    return session.get(EvaluationCase, case_id)


def _seed_case_without_url(session, *, case_id="case-nourl"):
    now = datetime.now(timezone.utc)
    session.execute(text(
        "INSERT INTO radar_mozare_routes (id, name, state, created_at, updated_at)"
        " VALUES ('route-nu', 'MA Programme', 'ACTIVE', :n, :n)"
    ), {"n": now})
    session.execute(text(
        "INSERT INTO radar_target_entities (id, kind, display_name, created_at, updated_at)"
        " VALUES ('t-nu', 'Programme', 'No URL', :n, :n)"
    ), {"n": now})
    session.execute(text(
        "INSERT INTO radar_evaluation_cases (id, route_id, target_id, application_route,"
        " research_state, user_disposition, application_stage, created_at, updated_at)"
        " VALUES (:cid, 'route-nu', 't-nu', 'MA_PROGRAMME', 'EVIDENCE_READY', 'ACT',"
        " 'APPLICATION_OPEN', :n, :n)"
    ), {"cid": case_id, "n": now})
    session.commit()
    return session.get(EvaluationCase, case_id)


@pytest.fixture
def ma_case(db_session):
    return _seed_ma_case(db_session)


class TestSourceUrls:
    def test_canonical_url_selected(self, db_session, ma_case):
        assert case_source_urls(db_session, ma_case) == ["https://example.com/programme"]

    def test_no_canonical_url_means_no_sources(self, db_session):
        case = _seed_case_without_url(db_session)
        assert case_source_urls(db_session, case) == []


class TestAcquire:
    def test_success_binds_snapshot_and_artifact(self, db_session, ma_case):
        outcome = acquire_case_evidence(db_session, ma_case, fetch_fn=lambda url, **kw: FakeResult())
        assert outcome["errors"] == []
        assert len(outcome["evidence_lookup"]) == 1
        artifact_id = next(iter(outcome["evidence_lookup"]))
        artifact = db_session.get(EvidenceArtifact, artifact_id)
        assert artifact is not None
        assert artifact.source_url == "https://example.com/programme"
        snap = db_session.get(SourceSnapshot, artifact.snapshot_id)
        assert snap is not None
        assert snap.state == "CAPTURED"

    def test_fetch_failure_records_fetch_failed_and_error(self, db_session, ma_case):
        outcome = acquire_case_evidence(
            db_session, ma_case,
            fetch_fn=lambda url, **kw: FakeResult(error="URL blocked by policy: private address"),
        )
        assert outcome["evidence_lookup"] == {}
        assert outcome["errors"]
        assert "blocked" in outcome["errors"][0]["error"]
        snaps = db_session.query(SourceSnapshot).filter(
            SourceSnapshot.source_url == "https://example.com/programme"
        ).all()
        assert snaps
        assert snaps[-1].state == "FETCH_FAILED"

    def test_deadline_check_fields_updated(self, db_session, ma_case):
        acquire_case_evidence(db_session, ma_case, fetch_fn=lambda url, **kw: FakeResult())
        prog = db_session.get(Programme, "prog-e1")
        assert prog.deadline_last_checked_at is not None
        assert prog.deadline_evidence_id is not None
        artifact = db_session.get(EvidenceArtifact, prog.deadline_evidence_id)
        assert artifact.source_url == "https://example.com/programme"

    def test_transport_crash_is_caught(self, db_session, ma_case):
        def boom(url, **kw):
            raise RuntimeError("transport exploded")

        outcome = acquire_case_evidence(db_session, ma_case, fetch_fn=boom)
        assert outcome["evidence_lookup"] == {}
        assert outcome["errors"][0]["error"] == "transport exploded"


class TestBindOrFail:
    def test_raises_when_nothing_bound(self, db_session, ma_case):
        with pytest.raises(ValueError) as exc:
            bind_or_fail(db_session, ma_case, fetch_fn=lambda url, **kw: FakeResult(error="blocked"))
        assert "No case-scoped evidence bound" in str(exc.value)

    def test_raises_when_no_sources_configured(self, db_session):
        case = _seed_case_without_url(db_session)
        with pytest.raises(ValueError):
            bind_or_fail(db_session, case, fetch_fn=lambda url, **kw: FakeResult())

    def test_returns_lookup_when_bound(self, db_session, ma_case):
        outcome = bind_or_fail(db_session, ma_case, fetch_fn=lambda url, **kw: FakeResult())
        assert len(outcome["evidence_lookup"]) == 1
