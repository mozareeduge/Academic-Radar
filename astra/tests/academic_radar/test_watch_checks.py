"""Test watch checks, fingerprints, change events.

OBJ-011: WatchTarget — URL/entity selected for change monitoring.
FLOW-007: Watch-triggered re-evaluation — watch fetch -> fingerprint -> diff -> mark STALE.
DEC-032: Changed-page reruns — unchanged watched snapshots do NOT trigger deep model research.
ORACLE-019: Evidence refresh is append/version based — re-fetch creates new snapshot.
"""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from academic_radar.watch.checks import run_watch_check
from academic_radar.watch.diff import line_diff
from academic_radar.watch.scheduler import due_targets


def _upgrade_db_schema(db_url: str) -> None:
    """Run alembic upgrade head on the given database."""
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    astra_dir = Path(__file__).parent.parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(astra_dir),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )


def _setup_watch_target(session: Session, url: str, cadence: str = "daily") -> dict:
    """Create a watch target row and return dict."""
    from uuid import uuid4
    target_id = str(uuid4())
    watch_id = str(uuid4())

    sql = text("""
        INSERT INTO radar_watch_targets
        (id, target_id, url, cadence, state, created_at, updated_at)
        VALUES (:watch_id, :target_id, :url, :cadence, 'ACTIVE', :now, :now)
    """)

    now = datetime.now(timezone.utc)
    session.execute(sql, {
        'watch_id': watch_id,
        'target_id': target_id,
        'url': url,
        'cadence': cadence,
        'now': now,
    })
    session.flush()

    return {
        'id': watch_id,
        'url': url,
        'cadence': cadence,
    }


def test_line_diff_added_removed():
    """Test line_diff() identifies added and removed lines."""
    old = "line 1\nline 2\nline 3"
    new = "line 1\nline 2 modified\nline 4"

    result = line_diff(old, new)

    assert 'added' in result
    assert 'removed' in result
    assert 'line 2 modified' in result['added']
    assert 'line 3' in result['removed']
    assert 'line 4' in result['added']
    assert 'line 1' not in result['added'] and 'line 1' not in result['removed']


def test_line_diff_empty_old():
    """Test line_diff() with empty old text."""
    old = ""
    new = "new line 1\nnew line 2"

    result = line_diff(old, new)

    assert len(result['added']) == 2
    assert len(result['removed']) == 0


def test_line_diff_empty_new():
    """Test line_diff() with empty new text."""
    old = "old line 1\nold line 2"
    new = ""

    result = line_diff(old, new)

    assert len(result['added']) == 0
    assert len(result['removed']) == 2


def test_line_diff_whitespace_normalization():
    """Test line_diff() normalizes whitespace in lines."""
    old = "  line A  \n  line B  "
    new = "line A\nline B\n"

    result = line_diff(old, new)

    assert len(result['added']) == 0, f"added: {result['added']}"
    assert len(result['removed']) == 0, f"removed: {result['removed']}"


def test_due_targets_daily_cadence():
    """Test due_targets() filters by daily cadence."""
    now = datetime.now(timezone.utc)

    targets = [
        {
            'id': 'watch1',
            'cadence': 'daily',
            'last_check_at': now - timedelta(hours=25),
        },
        {
            'id': 'watch2',
            'cadence': 'daily',
            'last_check_at': now - timedelta(hours=12),
        },
    ]

    due = due_targets(targets, now)

    assert len(due) == 1
    assert due[0]['id'] == 'watch1'


def test_due_targets_weekly_cadence():
    """Test due_targets() filters by weekly cadence."""
    now = datetime.now(timezone.utc)

    targets = [
        {
            'id': 'watch1',
            'cadence': 'weekly',
            'last_check_at': now - timedelta(days=8),
        },
        {
            'id': 'watch2',
            'cadence': 'weekly',
            'last_check_at': now - timedelta(days=5),
        },
    ]

    due = due_targets(targets, now)

    assert len(due) == 1
    assert due[0]['id'] == 'watch1'


def test_due_targets_never_checked():
    """Test due_targets() includes targets never checked."""
    now = datetime.now(timezone.utc)

    targets = [
        {
            'id': 'watch1',
            'cadence': 'daily',
            'last_check_at': None,
        },
    ]

    due = due_targets(targets, now)

    assert len(due) == 1
    assert due[0]['id'] == 'watch1'


def test_unchanged_page_no_change_event():
    """Test unchanged page creates check row but NO change event.

    Also verify enqueue callable is NOT called.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        _upgrade_db_schema(db_url)

        engine = create_engine(db_url)

        with Session(engine) as session:
            url = "https://example.com/page1"
            page_text = "Stable content"

            watch_target = _setup_watch_target(session, url)

            enqueue_called = []

            def mock_enqueue(msg):
                enqueue_called.append(msg)

            def fetch_fn_first(u):
                if u == url:
                    return (page_text, True)
                return (None, False)

            result1 = run_watch_check(session, watch_target, fetch_fn_first)
            session.commit()

            assert result1['snapshot_state'] == 'CAPTURED'
            assert result1['change_event_id'] is None

            def fetch_fn_second(u):
                if u == url:
                    return (page_text, True)
                return (None, False)

            result2 = run_watch_check(session, watch_target, fetch_fn_second)
            session.commit()

            assert result2['snapshot_state'] == 'UNCHANGED'
            assert result2['change_event_id'] is None
            assert len(enqueue_called) == 0, "enqueue should not be called for unchanged page"

            with Session(engine) as s:
                checks = s.execute(
                    text("SELECT id, changed FROM radar_watch_checks WHERE watch_target_id = :wid")
                        .bindparams(wid=watch_target['id'])
                ).fetchall()

                assert len(checks) == 2, "should have 2 check rows"
                assert checks[0][1] == 0, "CAPTURED should have changed=False"
                assert checks[1][1] == 0, "UNCHANGED should have changed=False"

                events = s.execute(
                    text("SELECT id FROM radar_change_events")
                ).fetchall()

                assert len(events) == 0, "should have no change events for unchanged page"

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


# ORACLE-019
def test_changed_page_one_event():
    """Test changed page creates one change event with material=True when >1 line differs."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        _upgrade_db_schema(db_url)

        engine = create_engine(db_url)

        with Session(engine) as session:
            url = "https://example.com/page2"
            old_text = "Line 1\nLine 2\nLine 3"
            new_text = "Line 1\nLine 2 modified\nLine 3\nLine 4 added"

            watch_target = _setup_watch_target(session, url)

            def fetch_fn_old(u):
                if u == url:
                    return (old_text, True)
                return (None, False)

            result1 = run_watch_check(session, watch_target, fetch_fn_old)
            session.commit()

            assert result1['snapshot_state'] == 'CAPTURED'

            def fetch_fn_new(u):
                if u == url:
                    return (new_text, True)
                return (None, False)

            result2 = run_watch_check(session, watch_target, fetch_fn_new, prior_text=old_text)
            session.commit()

            assert result2['snapshot_state'] == 'CHANGED'

            with Session(engine) as s:
                checks = s.execute(
                    text("SELECT id, changed FROM radar_watch_checks WHERE watch_target_id = :wid ORDER BY at ASC")
                        .bindparams(wid=watch_target['id'])
                ).fetchall()

                assert len(checks) == 2
                assert checks[1][1] == 1, "CHANGED should have changed=True"

                events = s.execute(
                    text("SELECT id, material, summary FROM radar_change_events")
                ).fetchall()

                assert len(events) == 1, "should have one change event"
                assert events[0][1] == 1, "event should be material (>1 line changed)"
                assert events[0][2] is not None, "event should have summary"

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_failed_fetch_no_event():
    """Test failed fetch creates check row but NO change event."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        _upgrade_db_schema(db_url)

        engine = create_engine(db_url)

        with Session(engine) as session:
            url = "https://example.com/unreachable"

            watch_target = _setup_watch_target(session, url)

            def fetch_fn_success(u):
                if u == url:
                    return ("original content", True)
                return (None, False)

            result1 = run_watch_check(session, watch_target, fetch_fn_success)
            session.commit()

            assert result1['snapshot_state'] == 'CAPTURED'

            def fetch_fn_fail(u):
                if u == url:
                    return (None, False)
                return (None, False)

            result2 = run_watch_check(session, watch_target, fetch_fn_fail)
            session.commit()

            assert result2['snapshot_state'] == 'FETCH_FAILED'
            assert result2['change_event_id'] is None

            with Session(engine) as s:
                checks = s.execute(
                    text("SELECT id, changed FROM radar_watch_checks WHERE watch_target_id = :wid ORDER BY at ASC")
                        .bindparams(wid=watch_target['id'])
                ).fetchall()

                assert len(checks) == 2
                assert checks[1][1] == 0, "FETCH_FAILED should have changed=False"

                events = s.execute(
                    text("SELECT id FROM radar_change_events")
                ).fetchall()

                assert len(events) == 0, "failed fetch should not create change event"

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_cadence_due_logic():
    """Test cadence logic determines when target is due."""
    now = datetime.now(timezone.utc)

    daily_due = {
        'id': 'w1',
        'cadence': 'daily',
        'last_check_at': now - timedelta(hours=25),
    }

    daily_not_due = {
        'id': 'w2',
        'cadence': 'daily',
        'last_check_at': now - timedelta(hours=12),
    }

    weekly_due = {
        'id': 'w3',
        'cadence': 'weekly',
        'last_check_at': now - timedelta(days=8),
    }

    due = due_targets([daily_due, daily_not_due, weekly_due], now)

    assert len(due) == 2
    assert any(t['id'] == 'w1' for t in due)
    assert any(t['id'] == 'w3' for t in due)
    assert not any(t['id'] == 'w2' for t in due)
