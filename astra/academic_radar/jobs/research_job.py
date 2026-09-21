"""RQ research worker and explicit provider configuration.

Only primitive configuration crosses the queue boundary. No provider object or
database engine is pickled into a job, and no empty mock is used in production.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.radar_models_evidence import ResearchRun

log = logging.getLogger(__name__)
MAX_RETRIES = 2
RETRY_BACKOFF_S = 1.0


def provider_config() -> dict[str, str]:
    """Select a provider explicitly; fixture mode is the sole mock path."""
    if os.environ.get("RADAR_FIXTURE_MODE") == "1":
        return {"provider_id": "fixture", "model_id": "fixture-script"}
    provider_id = os.environ.get("RADAR_RESEARCH_PROVIDER", "").strip().lower()
    model_id = os.environ.get("RADAR_RESEARCH_MODEL", "").strip()
    if provider_id != "litellm" or not model_id:
        raise ValueError("Set RADAR_RESEARCH_PROVIDER=litellm and RADAR_RESEARCH_MODEL")
    return {"provider_id": provider_id, "model_id": model_id}


def research_queue():
    """Return the dedicated RQ queue, requiring reachable Redis."""
    import redis
    from rq import Queue

    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        raise RuntimeError("REDIS_URL is required for research jobs")
    client = redis.from_url(url, socket_connect_timeout=0.5, socket_timeout=1.0)
    client.ping()
    return Queue("research", connection=client)


def enqueue_research(case_id: str, queue, run_key: str, run_id: str, config: dict[str, str]) -> str:
    """Submit one durable run using JSON-safe arguments only."""
    job = queue.enqueue(
        research_case_job,
        case_id,
        run_key,
        kwargs={"deps": {"run_id": run_id, "config": config}},
        job_id=f"research-{run_id}",
        result_ttl=3600,
        failure_ttl=86400,
    )
    return job.id


def research_case_job(case_id: str, run_key: str, *, deps: dict) -> Optional[dict]:
    """Advance QUEUED -> RUNNING -> COMPLETED/PARTIAL/FAILED on one row."""
    from db.init import resolve_db_url

    engine = deps.get("engine") or create_engine(resolve_db_url())
    run_id = deps["run_id"]
    config = deps["config"]
    sleep_fn = deps.get("sleep_fn", time.sleep)

    with Session(engine) as session:
        run = session.get(ResearchRun, run_id)
        if run is None or run.case_id != case_id or (run.run_identity or {}).get("run_key") != run_key:
            raise ValueError("Queued research run identity mismatch")
        if run.status in {"COMPLETED", "PARTIAL"}:
            return _serialize_run(run)
        if run.status == "CANCELLED":
            return None
        run.status = "RUNNING"
        session.commit()

        reason = "UNKNOWN"
        for attempt in range(MAX_RETRIES + 1):
            try:
                provider, evidence_lookup = _resolve_provider(session, case_id, config, deps)
                from academic_radar.research.service import run_research

                run_research(
                    session, case_id, provider, evidence_lookup,
                    run_key=run_key, run_id=run_id,
                    model_id=config["model_id"], provider_id=config["provider_id"],
                )
                session.refresh(run)
                return _serialize_run(run)
            except Exception as exc:
                session.rollback()
                reason = _failure_reason(exc)
                log.warning("research run %s attempt %s failed: %s", run_id, attempt + 1, reason)
                if attempt < MAX_RETRIES:
                    sleep_fn(RETRY_BACKOFF_S)

        run = session.get(ResearchRun, run_id)
        run.status = "FAILED"
        run.run_identity = {**(run.run_identity or {}), "failure_reason": reason}
        session.commit()
        return None


def _resolve_provider(session: Session, case_id: str, config: dict, deps: dict):
    if "provider" in deps:  # deterministic unit-test seam; never serialized by the API
        return deps["provider"], deps.get("evidence_lookup", {})
    if config["provider_id"] == "fixture":
        if os.environ.get("RADAR_FIXTURE_MODE") != "1":
            raise ValueError("Fixture provider disabled")
        from academic_radar.research.fixtures import fixture_evidence_and_provider
        from db.radar_models_cases import EvaluationCase

        case = session.get(EvaluationCase, case_id)
        if case is None:
            raise ValueError("Research case not found")
        return fixture_evidence_and_provider(session, case)
    if config["provider_id"] == "litellm":
        evidence_lookup = deps.get("evidence_lookup") or {}
        if not evidence_lookup:
            raise ValueError(
                "No case-scoped evidence bound to this run; "
                "evidence binding required before live research"
            )
        from academic_radar.research.provider import LiteLLMProvider

        return LiteLLMProvider(config["model_id"]), evidence_lookup
    raise ValueError("Unsupported research provider")


def _failure_reason(exc: Exception) -> str:
    if isinstance(exc, TimeoutError):
        return "PROVIDER_TIMEOUT"
    if isinstance(exc, ValueError):
        return "SOURCE_BLOCKED" if any(word in str(exc).lower() for word in ("blocked", "forbidden")) else "INVALID_OUTPUT"
    return "UNKNOWN"


def _serialize_run(run: ResearchRun) -> dict:
    return {"id": run.id, "case_id": run.case_id, "status": run.status}
