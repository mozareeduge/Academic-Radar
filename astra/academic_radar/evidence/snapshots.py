"""Snapshots and evidence artifacts (append-only).

OBJ-006: EvidenceArtifact — recoverable evidence unit.
OBJ-007: Snapshot — immutable observation of external source at a time.
DEC-011: Evidence versioning — external updates append snapshots, never destructively overwrite.
ORACLE-019: Evidence refresh is append/version based — re-fetch creates new snapshot; history preserved.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from academic_radar.domain.enums import SnapshotState


def fingerprint(text: str) -> str:
    """Compute sha256 of whitespace-normalized text.

    Normalization: collapse multiple spaces/newlines/tabs to single space,
    strip leading/trailing whitespace, then lowercase for case-insensitive comparison.
    """
    normalized = re.sub(r"\s+", " ", text.strip()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def record_snapshot(
    session: Session,
    url: str,
    text_or_none: Optional[str],
    fetched_ok: bool,
) -> "SnapshotRow":
    """Record a source snapshot (append-only).

    Creates a NEW radar_source_snapshots row every time with state:
    - CAPTURED: first fetch (no prior snapshot)
    - UNCHANGED: same fingerprint as previous for url
    - CHANGED: different fingerprint than previous for url
    - FETCH_FAILED: fetched_ok False, fingerprint null

    Never updates or deletes an existing snapshot row.

    Args:
        session: SQLAlchemy session
        url: source URL
        text_or_none: fetched text, or None if fetched_ok is False
        fetched_ok: whether fetch succeeded

    Returns:
        New SnapshotRow object (not yet committed)
    """
    now = datetime.now(timezone.utc)
    snapshot_id = str(uuid4())

    if not fetched_ok:
        new_state = SnapshotState.FETCH_FAILED
        new_fingerprint = None
    else:
        if text_or_none is None:
            raise ValueError("text_or_none must not be None when fetched_ok=True")

        new_fingerprint = fingerprint(text_or_none)

        prior = session.query(text(
            "fingerprint FROM radar_source_snapshots WHERE source_url = :url ORDER BY captured_at DESC LIMIT 1"
        )).params(url=url).scalar()

        if prior is None:
            new_state = SnapshotState.CAPTURED
        elif prior == new_fingerprint:
            new_state = SnapshotState.UNCHANGED
        else:
            new_state = SnapshotState.CHANGED

    insert_sql = text("""
        INSERT INTO radar_source_snapshots
        (id, source_url, fingerprint, state, content_ref, captured_at, created_at, updated_at)
        VALUES (:id, :url, :fp, :state, :ref, :at, :at, :at)
    """)

    session.execute(insert_sql, {
        "id": snapshot_id,
        "url": url,
        "fp": new_fingerprint,
        "state": new_state.value,
        "ref": None,
        "at": now,
    })

    row = SnapshotRow(
        id=snapshot_id,
        source_url=url,
        fingerprint=new_fingerprint,
        state=new_state.value,
        content_ref=None,
        captured_at=now,
        created_at=now,
        updated_at=now,
    )
    return row


class SnapshotRow:
    """Temporary holder for snapshot data until persisted."""
    def __init__(self, id, source_url, fingerprint, state, content_ref, captured_at, created_at, updated_at):
        self.id = id
        self.source_url = source_url
        self.fingerprint = fingerprint
        self.state = state
        self.content_ref = content_ref
        self.captured_at = captured_at
        self.created_at = created_at
        self.updated_at = updated_at
