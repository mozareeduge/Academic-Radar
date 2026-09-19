"""Test snapshots and evidence artifacts (append-only ledger).

OBJ-006: EvidenceArtifact — recoverable evidence unit with source URL, type, excerpt, snapshot ID, etc.
OBJ-007: Snapshot — immutable observation of external source. States: CAPTURED, UNCHANGED, CHANGED, FETCH_FAILED.
DEC-011: Evidence versioning — external updates append snapshots and invalidate dependent claims.
DEC-013: User correction — create or replace assessments with traceable history.
ORACLE-019: Evidence refresh is append/version based — re-fetch creates new snapshot, old state preserved.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from academic_radar.evidence.snapshots import fingerprint, record_snapshot
from academic_radar.evidence.artifacts import create_artifact


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


def test_fingerprint():
    """Test fingerprint() creates consistent sha256 of whitespace-normalized text."""
    text1 = "Hello   World  \n  Test"
    text2 = "Hello World Test"
    text3 = "Different content"

    fp1 = fingerprint(text1)
    fp2 = fingerprint(text2)
    fp3 = fingerprint(text3)

    assert len(fp1) == 64, "fingerprint should return sha256 hex (64 chars)"
    assert fp1 == fp2, "fingerprint should normalize whitespace"
    assert fp1 != fp3, "fingerprint should differ for different text"


# ORACLE-019
def test_snapshots_append_only():
    """Test record_snapshot() creates CAPTURED, UNCHANGED, CHANGED as separate rows.

    Three consecutive fetches of a URL with different content create three rows
    with states: CAPTURED (first), UNCHANGED (same text), CHANGED (different text).
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        _upgrade_db_schema(db_url)

        engine = create_engine(db_url)

        with Session(engine) as session:
            url = "https://example.com/page1"
            text_v1 = "Version 1 content here"
            text_v2 = "Same content"

            s1 = record_snapshot(session, url, text_v1, fetched_ok=True)
            session.flush()
            assert s1.state == "CAPTURED", "first fetch should be CAPTURED"
            assert s1.fingerprint == fingerprint(text_v1)

            s2 = record_snapshot(session, url, text_v1, fetched_ok=True)
            session.flush()
            assert s2.state == "UNCHANGED", "same text should be UNCHANGED"
            assert s2.fingerprint == fingerprint(text_v1)
            assert s1.id != s2.id, "should create separate rows"

            s3 = record_snapshot(session, url, text_v2, fetched_ok=True)
            session.flush()
            assert s3.state == "CHANGED", "different text should be CHANGED"
            assert s3.fingerprint == fingerprint(text_v2)
            assert s1.id != s3.id, "should create separate rows"

            session.commit()

        with Session(engine) as session:
            rows = session.execute(
                text("SELECT id, source_url, state, fingerprint FROM radar_source_snapshots WHERE source_url = :url ORDER BY created_at ASC").bindparams(url=url)
            ).fetchall()

            assert len(rows) == 3, "should have exactly 3 snapshot rows"
            assert rows[0][2] == "CAPTURED"
            assert rows[1][2] == "UNCHANGED"
            assert rows[2][2] == "CHANGED"

            old_fps = {rows[0][3], rows[1][3]}
            new_fp = rows[2][3]
            assert len(old_fps) == 1, "CAPTURED and UNCHANGED should have same fingerprint"
            assert new_fp not in old_fps, "CHANGED should have different fingerprint"

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_snapshot_fetch_failed():
    """Test record_snapshot() with fetched_ok=False yields FETCH_FAILED, no fingerprint."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        _upgrade_db_schema(db_url)

        engine = create_engine(db_url)

        with Session(engine) as session:
            url = "https://example.com/unreachable"

            s1 = record_snapshot(session, url, "original text", fetched_ok=True)
            session.flush()
            assert s1.state == "CAPTURED"

            s2 = record_snapshot(session, url, None, fetched_ok=False)
            session.flush()
            assert s2.state == "FETCH_FAILED", "failed fetch should be FETCH_FAILED"
            assert s2.fingerprint is None, "FETCH_FAILED should have null fingerprint"
            assert s1.id != s2.id, "should create new row"

            session.commit()

        with Session(engine) as session:
            rows = session.execute(
                text("SELECT id, source_url, state, fingerprint FROM radar_source_snapshots WHERE source_url = :url ORDER BY created_at ASC").bindparams(url=url)
            ).fetchall()

            assert len(rows) == 2, "should have 2 snapshot rows (CAPTURED and FETCH_FAILED)"
            assert rows[0][2] == "CAPTURED"
            assert rows[1][2] == "FETCH_FAILED"
            assert rows[1][3] is None, "FETCH_FAILED fingerprint should be null"

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_artifact_stores_authority_and_origin():
    """Test create_artifact() classifies authority via domain and stores canonical_origin."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        _upgrade_db_schema(db_url)

        engine = create_engine(db_url)

        with Session(engine) as session:
            url = "https://example.edu/programme/master"
            page_text = "Master Programme Description"

            snapshot = record_snapshot(session, url, page_text, fetched_ok=True)
            session.flush()

            artifact = create_artifact(
                session,
                snapshot,
                url,
                "text/html",
                "This is an excerpt of the programme",
                structured={"level": "masters", "field": "Computer Science"},
                published_at=datetime(2025, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
            )
            session.flush()

            assert artifact.source_url == url
            assert artifact.source_type == "text/html"
            assert artifact.excerpt == "This is an excerpt of the programme"
            assert artifact.structured_extraction == {"level": "masters", "field": "Computer Science"}
            assert artifact.published_at == datetime(2025, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
            assert artifact.snapshot_id == snapshot.id

            assert artifact.source_authority in (
                "OFFICIAL_REGULATION", "OFFICIAL_PROGRAMME", "OFFICIAL_DEPARTMENT_OR_PERSON",
                "AUTHORITATIVE_REGISTRY", "PRIMARY_RESEARCH_OUTPUT", "REPUTABLE_SECONDARY",
                "DISCOVERY_AGGREGATOR", "UNKNOWN"
            ), f"source_authority should be a valid enum value, got {artifact.source_authority}"

            assert artifact.canonical_origin is not None
            assert len(artifact.canonical_origin) == 64, "canonical_origin should be sha256 hex"

            session.commit()

        with Session(engine) as session:
            artifact_row = session.execute(
                text("SELECT id, snapshot_id, source_authority, canonical_origin FROM radar_evidence_artifacts WHERE source_url = :url").bindparams(url=url)
            ).first()

            assert artifact_row is not None
            assert artifact_row[1] == snapshot.id
            assert artifact_row[2] in (
                "OFFICIAL_REGULATION", "OFFICIAL_PROGRAMME", "OFFICIAL_DEPARTMENT_OR_PERSON",
                "AUTHORITATIVE_REGISTRY", "PRIMARY_RESEARCH_OUTPUT", "REPUTABLE_SECONDARY",
                "DISCOVERY_AGGREGATOR", "UNKNOWN"
            )
            assert artifact_row[3] is not None

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)
