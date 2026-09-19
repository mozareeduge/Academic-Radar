"""RQ wrapper for deep-research jobs with idempotency and provider error handling."""

import json
import logging
import time
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

# Max retries on provider error (2 additional attempts after initial)
MAX_RETRIES = 2
RETRY_BACKOFF_S = 1.0


def research_case_job(
    case_id: str,
    run_key: str,
    *,
    deps: dict,
) -> Optional[dict]:
    """Execute deep-research workflow with idempotency.

    This is the RQ worker entrypoint. It runs the nine-node LangGraph workflow
    for a case, idempotent on run_key: if a run with that key already has
    status COMPLETED it returns it without re-running.

    On provider error, retries at most MAX_RETRIES times via caller-injected
    sleep. After exhausting retries, records status FAILED with a classified
    failure reason (PROVIDER_TIMEOUT | INVALID_OUTPUT | SOURCE_BLOCKED |
    UNKNOWN).

    Never writes user_disposition.

    Args:
        case_id: The evaluation case ID.
        run_key: Idempotency key (usually derived from case_id + protocol).
        deps: Dict with 'provider' (LLMProvider), 'protocol' (ResearchProtocol),
              'evidence_lookup' (dict), 'engine' (optional, defaults to resolve_db_url()),
              and optional 'sleep_fn' (defaults to time.sleep).

    Returns:
        The graph result dict (claims, coverage, readiness) or None if the job failed.
    """
    sleep_fn = deps.get("sleep_fn", time.sleep)

    if "engine" in deps:
        engine = deps["engine"]
    else:
        from sqlalchemy import create_engine
        from db.init import resolve_db_url
        db_url = resolve_db_url()
        engine = create_engine(db_url)

    with Session(engine) as session:
        from db.radar_models_evidence import ResearchRun
        from academic_radar.research.graph import build_graph

        # Check idempotency: look for COMPLETED run with this run_key in run_identity
        existing = _find_run_by_key(session, case_id, run_key)
        if existing and existing.status == "COMPLETED":
            log.info(
                "research job %s (case=%s): run_key already COMPLETED, returning existing",
                run_key,
                case_id,
            )
            return _serialize_run(existing)

        # Get or create the run record
        if existing:
            run = existing
            run.status = "RUNNING"
        else:
            protocol_version = "unknown"
            if "protocol" in deps:
                protocol = deps["protocol"]
                if hasattr(protocol, "protocol_version"):
                    protocol_version = protocol.protocol_version
                elif hasattr(protocol, "version"):
                    protocol_version = protocol.version

            run = ResearchRun(
                case_id=case_id,
                status="RUNNING",
                protocol_version=protocol_version,
                run_identity={"run_key": run_key},
            )
            session.add(run)
        session.commit()

        # Now attempt the graph execution with retries
        provider = deps.get("provider")
        protocol = deps.get("protocol")
        evidence_lookup = deps.get("evidence_lookup", {})

        if not provider or not protocol:
            run.status = "FAILED"
            session.commit()
            log.error("research job %s: missing provider or protocol", run_key)
            return None

        graph = build_graph(provider, protocol, evidence_lookup)

        attempt = 0
        last_error_reason = None

        while attempt < MAX_RETRIES + 1:
            try:
                result = graph.invoke(
                    {
                        "case_state": {"case_id": case_id},
                        "sources": [],
                    }
                )
                # Success
                run.status = "COMPLETED"
                session.commit()
                log.info(
                    "research job %s (case=%s): completed successfully",
                    run_key,
                    case_id,
                )
                return result

            except TimeoutError as e:
                last_error_reason = "PROVIDER_TIMEOUT"
                attempt += 1
                if attempt <= MAX_RETRIES:
                    log.warning(
                        "research job %s: timeout on attempt %d/%d, retrying after backoff",
                        run_key,
                        attempt,
                        MAX_RETRIES + 1,
                    )
                    sleep_fn(RETRY_BACKOFF_S)
                else:
                    log.error(
                        "research job %s: PROVIDER_TIMEOUT after %d attempts",
                        run_key,
                        MAX_RETRIES + 1,
                    )

            except ValueError as e:
                # Classify ValueError — could be INVALID_OUTPUT or SOURCE_BLOCKED
                error_str = str(e).lower()
                if "blocked" in error_str or "forbidden" in error_str:
                    last_error_reason = "SOURCE_BLOCKED"
                else:
                    last_error_reason = "INVALID_OUTPUT"
                attempt += 1
                if attempt <= MAX_RETRIES:
                    log.warning(
                        "research job %s: %s on attempt %d/%d, retrying after backoff",
                        run_key,
                        last_error_reason,
                        attempt,
                        MAX_RETRIES + 1,
                    )
                    sleep_fn(RETRY_BACKOFF_S)
                else:
                    log.error(
                        "research job %s: %s after %d attempts",
                        run_key,
                        last_error_reason,
                        MAX_RETRIES + 1,
                    )

            except Exception as e:
                last_error_reason = "UNKNOWN"
                attempt += 1
                if attempt <= MAX_RETRIES:
                    log.warning(
                        "research job %s: %s on attempt %d/%d, retrying after backoff",
                        run_key,
                        str(e),
                        attempt,
                        MAX_RETRIES + 1,
                    )
                    sleep_fn(RETRY_BACKOFF_S)
                else:
                    log.error(
                        "research job %s: %s after %d attempts",
                        run_key,
                        str(e),
                        MAX_RETRIES + 1,
                    )

        # All retries exhausted
        run.status = "FAILED"
        session.commit()
        log.error(
            "research job %s: failed with reason=%s",
            run_key,
            last_error_reason or "UNKNOWN",
        )
        return None


def _find_run_by_key(session: Session, case_id: str, run_key: str) -> Optional["ResearchRun"]:
    """Find a ResearchRun by case_id and run_key stored in run_identity."""
    from db.radar_models_evidence import ResearchRun

    runs = session.scalars(
        select(ResearchRun).where(ResearchRun.case_id == case_id)
    ).all()
    for run in runs:
        if run.run_identity and isinstance(run.run_identity, dict):
            if run.run_identity.get("run_key") == run_key:
                return run
    return None


def enqueue_research(case_id: str, queue) -> str:
    """Enqueue a research job on the given RQ queue (named 'research').

    Args:
        case_id: The evaluation case ID.
        queue: The RQ Queue instance.

    Returns:
        The job ID.
    """
    from academic_radar.research.provider import MockProvider
    from academic_radar.research.protocol_loader import load_protocols

    # For now use a basic mock provider and protocol
    # In real use, these come from deps passed to the job
    provider = MockProvider({})
    protocols = load_protocols()
    protocol = protocols["SUPERVISOR_FIRST_PHD"]

    run_key = f"{case_id}:supervisor_v1"

    job = queue.enqueue(
        research_case_job,
        case_id,
        run_key,
        kwargs={
            "deps": {
                "provider": provider,
                "protocol": protocol,
                "evidence_lookup": {},
            }
        },
        job_id=f"research-{run_key}",
        result_ttl=3600,
        failure_ttl=86400,
    )
    return job.id


def _serialize_run(run) -> dict:
    """Serialize a ResearchRun for return."""
    return {
        "id": run.id,
        "case_id": run.case_id,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }
