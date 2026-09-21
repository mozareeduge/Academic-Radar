"""Case-scoped evidence acquisition and binding for non-fixture research.

R3 discovery: production research had no case-scoped evidence acquisition or
binding input, so a live model would receive no sources and could fabricate
coverage. This module closes that gap honestly:

- the candidate URL set comes only from case-scoped facts the owner's own
  database already holds (the target's canonical URL);
- every acquisition goes through the audited ``safe_fetch`` boundary
  (SSRF-checked, redirect-pinned, byte-capped) and lands as an append-only
  snapshot plus evidence artifact, exactly like watch and fixture evidence;
- a live research run may only start when the binding produced at least one
  artifact; callers must fail closed on an empty lookup.

Binding a fetched canonical source also updates the target's deadline check
fields (``deadline_last_checked_at`` / ``deadline_evidence_id``): fetching the
programme page IS the deadline check, recorded with its evidence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session

from academic_radar.evidence.snapshots import record_snapshot
from academic_radar.evidence.artifacts import create_artifact
from academic_radar.security.fetch import safe_fetch
from academic_radar.domain.enums import SnapshotState
from db.radar_models_cases import EvaluationCase
from db.radar_models_targets import Programme, RadarOpportunity, TargetEntity

log = logging.getLogger(__name__)

DEFAULT_FETCH = safe_fetch
DEFAULT_MAX_BYTES = 2_000_000
DEFAULT_TIMEOUT_S = 20


def case_source_urls(session: Session, case: EvaluationCase) -> list[str]:
    """Return the case-scoped candidate source URLs, deduplicated, in order.

    Currently: the case target's canonical URL. Kept deliberately narrow —
    watch targets are monitoring instruments, not research evidence, and the
    discovery path has no production source acquisition yet.
    """
    urls: list[str] = []
    target = session.query(TargetEntity).filter(
        TargetEntity.id == case.target_id
    ).one_or_none()
    if target and target.canonical_url:
        url = target.canonical_url.strip()
        if url:
            urls.append(url)
    return urls


def acquire_case_evidence(
    session: Session,
    case: EvaluationCase,
    *,
    fetch_fn: Optional[Callable] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Fetch case-scoped sources and bind them as evidence for this case.

    Every successful fetch appends a snapshot (CAPTURED/CHANGED/UNCHANGED per
    fingerprint history) and an evidence artifact classified by authority.
    A case target's ``deadline_last_checked_at``/``deadline_evidence_id`` is
    updated for its Programme/RadarOpportunity row when its canonical source
    is captured. Failures (blocked, HTTP error, oversize) are recorded as
    FETCH_FAILED snapshots and returned as errors — they never raise.

    Returns:
        dict with:
        - evidence_lookup: {artifact_id: {"url", "class"}} for artifacts
          created or already bound from a successful fetch this call;
        - errors: [{url, error}] for failed fetches.
    """
    fetch = fetch_fn or DEFAULT_FETCH
    evidence_lookup: dict = {}
    errors: list[dict] = []

    for url in case_source_urls(session, case):
        try:
            result = fetch(url, max_bytes=max_bytes, timeout_s=timeout_s)
        except Exception as exc:  # defensive: a broken transport must not kill the run
            log.warning("evidence fetch crashed for %s: %s", url, exc)
            errors.append({"url": url, "error": str(exc)})
            continue

        if result.error or result.body_bytes is None:
            log.info("evidence fetch failed for %s: %s", url, result.error)
            record_snapshot(session, url, None, False)
            errors.append({"url": url, "error": result.error or "no body"})
            continue

        try:
            text = result.body_bytes.decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - decode with replace cannot fail
            errors.append({"url": url, "error": str(exc)})
            continue

        snapshot = record_snapshot(session, url, text, True)
        artifact = create_artifact(
            session,
            snapshot=snapshot,
            source_url=url,
            source_type=result.content_type or "text/html",
            excerpt=text[:4000],
        )
        evidence_lookup[artifact.id] = {"url": url, "class": "TARGET_CANONICAL"}

        _mark_target_checked(session, case, artifact.id)

    session.flush()
    return {"evidence_lookup": evidence_lookup, "errors": errors}


def _mark_target_checked(session: Session, case: EvaluationCase, evidence_id: str) -> None:
    """Record that the target's canonical source was fetched with evidence."""
    now = datetime.now(timezone.utc)
    if case.application_route == "MA_PROGRAMME":
        row = session.query(Programme).filter(
            Programme.target_entity_id == case.target_id
        ).one_or_none()
    elif case.application_route in ("ADVERTISED_PHD", "STRUCTURED_PHD", "SUPERVISOR_FIRST_PHD"):
        row = session.query(RadarOpportunity).filter(
            RadarOpportunity.target_entity_id == case.target_id
        ).one_or_none()
    else:
        return
    if row is not None:
        row.deadline_last_checked_at = now
        row.deadline_evidence_id = evidence_id


def bind_or_fail(session: Session, case: EvaluationCase, **kwargs) -> dict:
    """Acquire case evidence and fail closed when nothing bound.

    Raises ValueError when no case-scoped evidence could be acquired, so a
    live provider can never run sourceless. The exception message matches the
    R3 worker's SOURCE_BLOCKED classification vocabulary only if the failure
    is a policy block; otherwise it is a plain contract failure.
    """
    outcome = acquire_case_evidence(session, case, **kwargs)
    if not outcome["evidence_lookup"]:
        reasons = "; ".join(f"{e['url']}: {e['error']}" for e in outcome["errors"]) or "no case-scoped sources configured"
        raise ValueError(f"No case-scoped evidence bound to this run; evidence binding required before live research ({reasons})")
    return outcome
