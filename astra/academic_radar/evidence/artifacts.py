"""Evidence artifacts — source units with authority classification and origin grouping.

OBJ-006: EvidenceArtifact — recoverable evidence unit with source URL, type, excerpt, snapshot, authority, origin.
DEC-038: Copied evidence is not independent — grouped by canonical-origin, not counted as separate evidence.
ORACLE-015: Repeated sources do not fake corroboration — syndicated statements sharing canonical origin count as one.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from academic_radar.domain.authority import classify_source, origin_group


def create_artifact(
    session: Session,
    snapshot: Any,
    source_url: str,
    source_type: str,
    excerpt: str,
    structured: Optional[dict[str, Any]] = None,
    published_at: Optional[datetime] = None,
) -> "ArtifactRow":
    """Create an evidence artifact with authority classification and origin grouping.

    Uses domain.authority.classify_source to determine authority level based on URL.
    Uses origin_group to store canonical_origin (sha256 of normalized text excerpt),
    enabling syndication detection.

    Args:
        session: SQLAlchemy session
        snapshot: SnapshotRow with id and source_url
        source_url: URL of source
        source_type: MIME type or description (e.g., "text/html", "application/pdf")
        excerpt: text excerpt from source
        structured: optional dict of structured extraction (JSON)
        published_at: optional publication/effective date

    Returns:
        ArtifactRow (not yet committed)
    """
    now = datetime.now(timezone.utc)
    artifact_id = str(uuid4())

    authority = classify_source(source_url)
    canonical = origin_group(source_url, excerpt)

    insert_sql = text("""
        INSERT INTO radar_evidence_artifacts
        (id, source_url, source_type, excerpt, structured_extraction,
         snapshot_id, retrieved_at, published_at, source_authority,
         canonical_origin, identity_confidence, created_at, updated_at)
        VALUES (:id, :url, :type, :excerpt, :structured, :snap_id,
                :retrieved, :published, :authority, :origin, :conf, :at, :at)
    """)

    session.execute(insert_sql, {
        "id": artifact_id,
        "url": source_url,
        "type": source_type,
        "excerpt": excerpt,
        "structured": json.dumps(structured) if structured else None,
        "snap_id": snapshot.id,
        "retrieved": now,
        "published": published_at,
        "authority": authority.value,
        "origin": canonical,
        "conf": None,
        "at": now,
    })

    row = ArtifactRow(
        id=artifact_id,
        source_url=source_url,
        source_type=source_type,
        excerpt=excerpt,
        structured_extraction=structured,
        snapshot_id=snapshot.id,
        retrieved_at=now,
        published_at=published_at,
        source_authority=authority.value,
        canonical_origin=canonical,
        identity_confidence=None,
        created_at=now,
        updated_at=now,
    )
    return row


class ArtifactRow:
    """Temporary holder for artifact data until persisted."""
    def __init__(
        self,
        id,
        source_url,
        source_type,
        excerpt,
        structured_extraction,
        snapshot_id,
        retrieved_at,
        published_at,
        source_authority,
        canonical_origin,
        identity_confidence,
        created_at,
        updated_at,
    ):
        self.id = id
        self.source_url = source_url
        self.source_type = source_type
        self.excerpt = excerpt
        self.structured_extraction = structured_extraction
        self.snapshot_id = snapshot_id
        self.retrieved_at = retrieved_at
        self.published_at = published_at
        self.source_authority = source_authority
        self.canonical_origin = canonical_origin
        self.identity_confidence = identity_confidence
        self.created_at = created_at
        self.updated_at = updated_at
