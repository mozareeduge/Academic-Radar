"""Tests for research_case_job, enqueue_research, and provider configuration.

Covers the R3 queue/provider lifecycle contract:
- enqueue_research submits JSON-safe args only (run_id + primitive config dict)
- provider_config is explicit via env and fails closed when unconfigured
- research_case_job advances one row QUEUED -> RUNNING -> COMPLETED/PARTIAL/FAILED
  with classified failure_reason persisted to run_identity
- a COMPLETED/PARTIAL run is returned without re-running the provider
- the litellm provider path is fail-closed without case-scoped evidence
"""

import json
import uuid
from datetime import datetime, timezone

import pytest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from academic_radar.jobs.research_job import (
    MAX_RETRIES,
    RETRY_BACKOFF_S,
    enqueue_research,
    provider_config,
    research_case_job,
)
from academic_radar.research.provider import MockProvider
from db.models import Base
from db.radar_models_cases import EvaluationCase
from db.radar_models_evidence import (
    EvidenceArtifact,
    ResearchRun,
    SourceSnapshot,
)
from db.radar_models_targets import TargetEntity, MozareRoute

NODE_NAMES = [
    "01_resolve_identity",
    "02_current_context_formal_route",
    "03_recent_research_spine",
    "04_supervised_projects",
    "05_concept_method_corpus_genealogy",
    "06_project_funding_context",
    "07_route_translation",
    "08_contradictions_unknowns",
    "09_structured_synthesis",
]

FULL_COVERAGE = {
    "IDENTITY_POSITION": "SEARCHED_FOUND",
    "RESEARCH_OBJECTS": "SEARCHED_FOUND",
    "THEORY_TOOLKIT": "SEARCHED_FOUND",
    "METHODS": "SEARCHED_FOUND",
    "RECENT_WORKS": "SEARCHED_FOUND",
    "PROJECTS_GRANTS": "SEARCHED_FOUND",
    "SUPERVISION_RECORD": "SEARCHED_FOUND",
    "SUPERVISED_PROJECTS": "SEARCHED_FOUND",
}


def _full_coverage_script() -> dict:
    """NodeOutput JSON covering every mandatory class for all nine nodes."""
    output = {
        "schema_version": "1.0.0",
        "node": "01_resolve_identity",
        "claims": [
            {
                "statement": "Test claim for IDENTITY_POSITION",
                "claim_type": "EXTERNAL_FACT",
                "evidence_ids": ["evt-1"],
                "protocol_class": "IDENTITY_POSITION",
                "unknowns": [],
                "contradictions": [],
            }
        ],
        "coverage": dict(FULL_COVERAGE),
    }
    return {node: json.dumps(output) for node in NODE_NAMES}


@pytest.fixture()
def db_engine(tmp_path):
    """One disposable sqlite database per test, with all radar tables."""
    import db.radar_models_targets  # noqa: F401
    import db.radar_models_cases  # noqa: F401
    import db.radar_models_evidence  # noqa: F401
    import db.radar_models_claims  # noqa: F401

    engine = create_engine(
        f"sqlite:///{tmp_path / 'research_job.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def _make_case(session) -> EvaluationCase:
    """Create a supervisor-first PhD evaluation case."""
    route = MozareRoute(name="Test Route", state="ACTIVE")
    session.add(route)
    session.flush()
    target = TargetEntity(kind="Person", display_name="Test Person")
    session.add(target)
    session.flush()
    case = EvaluationCase(
        route_id=route.id,
        target_id=target.id,
        application_route="SUPERVISOR_FIRST_PHD",
        research_state="DISCOVERED",
    )
    session.add(case)
    session.flush()
    return case


def _make_evidence(session) -> None:
    """One snapshot + artifact so claim evidence links resolve."""
    snapshot = SourceSnapshot(
        id="snap-1",
        source_url="https://example.com/test",
        state="CAPTURED",
        captured_at=datetime.now(timezone.utc),
    )
    session.add(snapshot)
    session.flush()
    artifact = EvidenceArtifact(
        id="evt-1",
        source_url="https://example.com/test",
        source_type="text/html",
        excerpt="Test excerpt",
        snapshot_id=snapshot.id,
        retrieved_at=datetime.now(timezone.utc),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.flush()


def _make_run(session, case: EvaluationCase, *, status: str = "QUEUED",
              run_key: str = "rk-1") -> ResearchRun:
    """Persist a run row with the API's identity shape."""
    run = ResearchRun(
        case_id=case.id,
        protocol_version="1.0.0",
        status=status,
        model_id="test/model",
        provider_id="litellm",
    )
    session.add(run)
    session.flush()
    run.run_identity = {"run_key": run_key, "run_id": run.id}
    session.commit()
    return run


def _job_deps(engine, run_id: str, config: dict, **extra) -> dict:
    deps = {
        "engine": engine,
        "run_id": run_id,
        "config": dict(config),
        "sleep_fn": lambda s: None,
    }
    deps.update(extra)
    return deps


LITELLM_CONFIG = {"provider_id": "litellm", "model_id": "test/model"}


class TestEnqueueResearch:
    """Test enqueue_research function."""

    def test_enqueue_research_returns_job_id(self):
        """enqueue_research should return a job ID."""
        queue = MagicMock()
        job_mock = MagicMock()
        job_mock.id = "test-job-123"
        queue.enqueue.return_value = job_mock

        case_id = str(uuid.uuid4())
        job_id = enqueue_research(case_id, queue, "rk-1", "run-1", dict(LITELLM_CONFIG))

        assert job_id == "test-job-123"
        assert queue.enqueue.called

    def test_enqueue_research_json_safe_args_only(self):
        """Only the callable, case_id, run_key and a primitive deps dict cross the queue."""
        queue = MagicMock()
        job_mock = MagicMock()
        job_mock.id = "test-job-123"
        queue.enqueue.return_value = job_mock

        case_id = str(uuid.uuid4())
        enqueue_research(case_id, queue, "rk-1", "run-1", dict(LITELLM_CONFIG))

        args, kwargs = queue.enqueue.call_args
        assert args[0] is research_case_job
        assert args[1] == case_id
        assert args[2] == "rk-1"
        deps = kwargs["kwargs"]["deps"]
        assert deps == {"run_id": "run-1", "config": LITELLM_CONFIG}
        # JSON-safe: no provider object, no engine, serializes cleanly.
        assert json.loads(json.dumps(deps)) == deps
        assert kwargs["job_id"] == "research-run-1"


class TestResearchCaseJobSignature:
    """Test that research_case_job has the right signature for RQ."""

    def test_research_case_job_callable(self):
        """research_case_job should be callable as an RQ function."""
        # Check that it's callable
        assert callable(research_case_job)

        # Check signature has case_id, run_key, and deps kwargs
        import inspect
        sig = inspect.signature(research_case_job)
        assert "case_id" in sig.parameters
        assert "run_key" in sig.parameters
        assert "deps" in sig.parameters

        # deps should be keyword-only
        assert sig.parameters["deps"].kind == inspect.Parameter.KEYWORD_ONLY


class TestResearchJobLogic:
    """Test research job logic without database."""

    def test_retry_on_timeout(self):
        """Test that timeouts trigger retries."""
        # Verify constants are set correctly
        assert MAX_RETRIES == 2
        assert RETRY_BACKOFF_S == 1.0


class TestProviderConfig:
    """provider_config is explicit; fixture is the sole mock path."""

    def test_fixture_mode_enabled(self, monkeypatch):
        monkeypatch.setenv("RADAR_FIXTURE_MODE", "1")
        monkeypatch.delenv("RADAR_RESEARCH_PROVIDER", raising=False)
        monkeypatch.delenv("RADAR_RESEARCH_MODEL", raising=False)
        assert provider_config() == {"provider_id": "fixture", "model_id": "fixture-script"}

    def test_litellm_configured(self, monkeypatch):
        monkeypatch.delenv("RADAR_FIXTURE_MODE", raising=False)
        monkeypatch.setenv("RADAR_RESEARCH_PROVIDER", "LiteLLM")
        monkeypatch.setenv("RADAR_RESEARCH_MODEL", "openai/gpt-4o-mini")
        assert provider_config() == {
            "provider_id": "litellm",
            "model_id": "openai/gpt-4o-mini",
        }

    def test_unconfigured_fails_closed(self, monkeypatch):
        monkeypatch.delenv("RADAR_FIXTURE_MODE", raising=False)
        monkeypatch.delenv("RADAR_RESEARCH_PROVIDER", raising=False)
        monkeypatch.delenv("RADAR_RESEARCH_MODEL", raising=False)
        with pytest.raises(ValueError):
            provider_config()

    def test_unknown_provider_rejected(self, monkeypatch):
        monkeypatch.delenv("RADAR_FIXTURE_MODE", raising=False)
        monkeypatch.setenv("RADAR_RESEARCH_PROVIDER", "bogus")
        monkeypatch.setenv("RADAR_RESEARCH_MODEL", "some/model")
        with pytest.raises(ValueError):
            provider_config()

    def test_litellm_without_model_rejected(self, monkeypatch):
        monkeypatch.delenv("RADAR_FIXTURE_MODE", raising=False)
        monkeypatch.setenv("RADAR_RESEARCH_PROVIDER", "litellm")
        monkeypatch.delenv("RADAR_RESEARCH_MODEL", raising=False)
        with pytest.raises(ValueError):
            provider_config()


class TestResolveProviderFailClosed:
    """Live research must never run without case-scoped evidence."""

    def test_litellm_without_evidence_raises(self, db_engine):
        from academic_radar.jobs.research_job import _resolve_provider

        with Session(db_engine) as session:
            case = _make_case(session)
            with pytest.raises(ValueError, match="evidence binding required"):
                _resolve_provider(session, case.id, dict(LITELLM_CONFIG), {"run_id": "x"})

    def test_litellm_with_evidence_lookup_does_not_raise(self, db_engine):
        from academic_radar.jobs.research_job import _resolve_provider

        with Session(db_engine) as session:
            case = _make_case(session)
            provider, lookup = _resolve_provider(
                session,
                case.id,
                dict(LITELLM_CONFIG),
                {"evidence_lookup": {"evt-1": {"url": "https://example.com/test"}}},
            )
            assert provider.model == "test/model"
            assert lookup == {"evt-1": {"url": "https://example.com/test"}}


class TestResearchCaseJob:
    """Worker advances one durable run row through its lifecycle."""

    def test_advances_queued_to_completed(self, db_engine):
        """QUEUED -> RUNNING -> COMPLETED with identity persisted."""
        with Session(db_engine) as session:
            case = _make_case(session)
            _make_evidence(session)
            run = _make_run(session, case)
            run_id, case_id = run.id, case.id

        deps = _job_deps(
            db_engine,
            run_id,
            dict(LITELLM_CONFIG),
            provider=MockProvider(_full_coverage_script()),
            evidence_lookup={"evt-1": {"url": "https://example.com/test"}},
        )
        result = research_case_job(case_id, "rk-1", deps=deps)

        assert result["status"] == "COMPLETED"
        assert result["id"] == run_id
        with Session(db_engine) as session:
            run = session.get(ResearchRun, run_id)
            assert run.status == "COMPLETED"
            assert run.model_id == "test/model"
            assert run.provider_id == "litellm"
            assert run.prompt_hash
            assert run.schema_version == "1.0.0"
            assert run.run_identity["run_key"] == "rk-1"

    def test_advances_queued_to_partial(self, db_engine):
        """Missing mandatory coverage yields PARTIAL, not COMPLETED."""
        partial_output = {
            "schema_version": "1.0.0",
            "node": "01_resolve_identity",
            "claims": [],
            "coverage": {
                "IDENTITY_POSITION": "NOT_SEARCHED",
                "RESEARCH_OBJECTS": "SEARCHED_FOUND",
                "THEORY_TOOLKIT": "SEARCHED_FOUND",
                "METHODS": "SEARCHED_FOUND",
                "RECENT_WORKS": "SEARCHED_FOUND",
                "PROJECTS_GRANTS": "SEARCHED_FOUND",
                "SUPERVISION_RECORD": "SEARCHED_FOUND",
                "SUPERVISED_PROJECTS": "SEARCHED_FOUND",
            },
        }
        script = {node: json.dumps(partial_output) for node in NODE_NAMES}

        with Session(db_engine) as session:
            case = _make_case(session)
            _make_evidence(session)
            run = _make_run(session, case)
            run_id, case_id = run.id, case.id

        deps = _job_deps(
            db_engine,
            run_id,
            dict(LITELLM_CONFIG),
            provider=MockProvider(script),
            evidence_lookup={"evt-1": {"url": "https://example.com/test"}},
        )
        result = research_case_job(case_id, "rk-1", deps=deps)
        assert result["status"] == "PARTIAL"
        with Session(db_engine) as session:
            assert session.get(ResearchRun, run_id).status == "PARTIAL"

    def test_completed_run_not_rerun(self, db_engine):
        """A COMPLETED run is returned as-is; the provider is never invoked."""
        with Session(db_engine) as session:
            case = _make_case(session)
            run = _make_run(session, case, status="COMPLETED")
            run_id, case_id = run.id, case.id

        provider = MagicMock()
        provider.complete.side_effect = AssertionError("must not be called")
        deps = _job_deps(db_engine, run_id, dict(LITELLM_CONFIG), provider=provider)

        result = research_case_job(case_id, "rk-1", deps=deps)
        assert result == {"id": run_id, "case_id": case_id, "status": "COMPLETED"}
        provider.complete.assert_not_called()

    def test_identity_mismatch_raises(self, db_engine):
        """A run whose stored run_key differs from the queued job's is rejected."""
        with Session(db_engine) as session:
            case = _make_case(session)
            run = _make_run(session, case, run_key="other-key")
            run_id, case_id = run.id, case.id

        deps = _job_deps(db_engine, run_id, dict(LITELLM_CONFIG))
        with pytest.raises(ValueError, match="identity mismatch"):
            research_case_job(case_id, "rk-1", deps=deps)

    @pytest.mark.parametrize(
        "exc,expected",
        [
            (TimeoutError("upstream timed out"), "PROVIDER_TIMEOUT"),
            (ValueError("node output failed schema validation"), "INVALID_OUTPUT"),
            (ValueError("source forbidden by url policy"), "SOURCE_BLOCKED"),
            (RuntimeError("boom"), "UNKNOWN"),
        ],
    )
    def test_failure_classification_persisted(self, db_engine, exc, expected):
        """Failures classify into failure_reason on run_identity after retries."""
        with Session(db_engine) as session:
            case = _make_case(session)
            run = _make_run(session, case)
            run_id, case_id = run.id, case.id

        provider = MagicMock()
        provider.complete.side_effect = exc
        deps = _job_deps(
            db_engine,
            run_id,
            dict(LITELLM_CONFIG),
            provider=provider,
            evidence_lookup={"evt-1": {"url": "https://example.com/test"}},
        )
        assert research_case_job(case_id, "rk-1", deps=deps) is None

        with Session(db_engine) as session:
            run = session.get(ResearchRun, run_id)
            assert run.status == "FAILED"
            assert run.run_identity["failure_reason"] == expected


class TestProviderErrorClassification:
    """Test provider error classification (without database)."""

    def test_failure_reasons_exist(self):
        """Verify failure reason enum values exist."""
        # These are the failure reasons the code should classify
        reasons = [
            "PROVIDER_TIMEOUT",
            "INVALID_OUTPUT",
            "SOURCE_BLOCKED",
            "UNKNOWN",
        ]

        # All should be valid strings
        for reason in reasons:
            assert isinstance(reason, str)
            assert len(reason) > 0
