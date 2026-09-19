"""Watch check execution and change event recording.

OBJ-011: WatchTarget — URL/entity selected for change monitoring.
FLOW-007: Watch-triggered re-evaluation — fetch -> fingerprint -> diff -> map impact.
DEC-032: Changed-page reruns — unchanged snapshots do not trigger deep model research.
"""

from datetime import datetime, timezone
from typing import Callable, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from academic_radar.evidence.snapshots import record_snapshot
from academic_radar.watch.diff import line_diff


def run_watch_check(
    session: Session,
    watch_target: dict,
    fetch_fn: Callable[[str], tuple[Optional[str], bool]],
    prior_text: Optional[str] = None,
) -> dict:
    """Execute a watch check for one target and record results.

    Calls fetch_fn(url) which returns (text_or_none, fetched_ok).
    Records snapshot via evidence.snapshots.record_snapshot.
    Writes radar_watch_checks row.
    If snapshot state is CHANGED and material change (>1 line), writes radar_change_events row.

    Args:
        session: SQLAlchemy session
        watch_target: dict with 'id' (watch_target_id) and 'url'
        fetch_fn: callable(url) -> (text_or_none, fetched_ok)
        prior_text: optional prior content for diff (if not provided, tries to fetch from DB)

    Returns:
        dict with keys:
        - 'watch_check_id': id of recorded check
        - 'snapshot_id': id of recorded snapshot
        - 'snapshot_state': 'CAPTURED', 'UNCHANGED', 'CHANGED', or 'FETCH_FAILED'
        - 'change_event_id': id of change event if material change, else None
        - 'summary': change summary if event, else None
    """
    url = watch_target['url']
    watch_target_id = watch_target['id']

    text_content, fetched_ok = fetch_fn(url)

    snapshot = record_snapshot(session, url, text_content, fetched_ok)
    session.flush()

    now = datetime.now(timezone.utc)

    check_sql = text("""
        INSERT INTO radar_watch_checks
        (id, watch_target_id, snapshot_id, changed, at, created_at, updated_at)
        VALUES (:check_id, :watch_id, :snap_id, :changed, :at, :at, :at)
    """)

    check_id = _generate_uuid()
    is_changed = snapshot.state == "CHANGED"

    session.execute(check_sql, {
        'check_id': check_id,
        'watch_id': watch_target_id,
        'snap_id': snapshot.id,
        'changed': is_changed,
        'at': now,
    })
    session.flush()

    result = {
        'watch_check_id': check_id,
        'snapshot_id': snapshot.id,
        'snapshot_state': snapshot.state,
        'change_event_id': None,
        'summary': None,
    }

    if snapshot.state == "CHANGED" and fetched_ok and text_content is not None:
        old_content = prior_text if prior_text is not None else _get_prior_snapshot_text(session, url)
        if old_content is not None:
            diff = line_diff(old_content, text_content)
            added = diff['added']
            removed = diff['removed']

            changed_lines_count = len(added) + len(removed)

            material = changed_lines_count > 1

            if material:
                summary = _summarize_diff(added, removed)
                event_sql = text("""
                    INSERT INTO radar_change_events
                    (id, watch_check_id, summary, material, at, created_at, updated_at)
                    VALUES (:event_id, :check_id, :summary, :material, :at, :at, :at)
                """)

                event_id = _generate_uuid()
                session.execute(event_sql, {
                    'event_id': event_id,
                    'check_id': check_id,
                    'summary': summary,
                    'material': True,
                    'at': now,
                })
                session.flush()

                result['change_event_id'] = event_id
                result['summary'] = summary

    return result


def _generate_uuid() -> str:
    """Generate a UUID string."""
    from uuid import uuid4
    return str(uuid4())


def _get_prior_snapshot_text(session: Session, url: str) -> Optional[str]:
    """Retrieve the text content of the prior snapshot for a URL.

    This is a temporary implementation that reconstructs content from the two
    most recent snapshots. In production, content_ref would point to versioned
    storage, but for testing we synthesize diff content.

    For now, returns None since schema doesn't store full content yet.
    """
    return None


def _summarize_diff(added: list[str], removed: list[str]) -> str:
    """Create a short summary of the first 3 differing lines.

    Includes up to 3 added/removed lines in the summary text.

    Args:
        added: list of added lines
        removed: list of removed lines

    Returns:
        short text summary of changes
    """
    parts = []

    if removed:
        parts.append(f"Removed: {'; '.join(removed[:3])}")

    if added:
        parts.append(f"Added: {'; '.join(added[:3])}")

    return "; ".join(parts)
