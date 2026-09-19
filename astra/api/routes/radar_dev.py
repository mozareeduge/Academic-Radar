"""api.routes.radar_dev — Radar fixture/dev endpoints (fixture mode only).

Implements /api/radar/dev/* endpoints for fixture-backed testing:
- import-seed: import synthetic seed profile/routes
- discovery: run fixture discovery
- discovery-status: poll discovery progress
- research: trigger research job with mock provider
- research-status: poll research job status
- simulate-change: create a change event on a watch
- (only available when RADAR_FIXTURE_MODE=1)
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.deps import get_db
from academic_radar.profile.mozare_import import import_seed
from db.radar_models_cases import EvaluationCase
from db.radar_models_targets import MozareRoute, CandidateProfile, TargetEntity
from db.radar_models_watch import WatchTarget, ChangeEvent, ApplicationBrief

router = APIRouter(prefix="/api/radar/dev", tags=["radar-dev"])


def _fixture_mode_only() -> None:
    """Raise 404 if not in fixture mode."""
    if os.environ.get("RADAR_FIXTURE_MODE") != "1":
        raise HTTPException(status_code=404, detail="Fixture mode disabled")


class ImportSeedRequest(BaseModel):
    """Request to import seed file."""
    seed_path: str = Field(..., description="Path to YAML seed file")


class ImportSeedResponse(BaseModel):
    """Response from seed import."""
    profile_id: str
    routes_created: int
    success: bool


@router.post("/import-seed", response_model=ImportSeedResponse)
def import_seed_endpoint(
    req: ImportSeedRequest,
    session: Session = Depends(get_db),
) -> ImportSeedResponse:
    """Import candidate profile and routes from YAML seed.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    seed_path = Path(req.seed_path)
    if not seed_path.is_absolute():
        # Relative to repo root
        seed_path = Path(__file__).parent.parent.parent.parent / seed_path

    if not seed_path.exists():
        raise HTTPException(status_code=400, detail=f"Seed file not found: {seed_path}")

    try:
        report = import_seed(seed_path, session)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

    # Extract profile_id from the import (assumes first profile created/updated)
    profile_id = None
    if report.profiles_created > 0 or report.profiles_updated > 0:
        from db.radar_models_targets import CandidateProfile
        profile = session.query(CandidateProfile).order_by(
            CandidateProfile.created_at.desc()
        ).first()
        if profile:
            profile_id = profile.id

    if not profile_id:
        raise HTTPException(status_code=400, detail="No profile was imported")

    return ImportSeedResponse(
        profile_id=profile_id,
        routes_created=report.routes_created,
        success=len(report.errors) == 0,
    )


class DiscoveryRequest(BaseModel):
    """Request to run discovery."""
    profile_id: str


class DiscoveryResponse(BaseModel):
    """Response from discovery start."""
    run_id: str


@router.post("/discovery", response_model=DiscoveryResponse)
def run_discovery(
    req: DiscoveryRequest,
    session: Session = Depends(get_db),
) -> DiscoveryResponse:
    """Start fixture discovery for a profile.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    # Verify profile exists
    profile = session.query(CandidateProfile).filter_by(id=req.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {req.profile_id}")

    # Create a discovery run (simplified; real implementation orchestrates the job)
    run_id = str(uuid4())
    now = datetime.now(timezone.utc)

    # In fixture mode, use mock discovery data
    # For now, just create placeholder entities
    for i in range(3):
        entity_type = ["Person", "Programme", "Institution"][i % 3]
        entity = TargetEntity(
            id=str(uuid4()),
            kind=entity_type,
            display_name=f"Fixture Entity {i+1}",
            canonical_url=f"http://example.com/{entity_type.lower()}/{i+1}",
            source_authority="DISCOVERY_AGGREGATOR",
        )
        session.add(entity)

    session.commit()

    return DiscoveryResponse(run_id=run_id)


class DiscoveryStatusResponse(BaseModel):
    """Status of a discovery run."""
    status: str  # completed, failed, pending
    entity_count: int = 0
    error: Optional[str] = None


@router.get("/discovery-status/{run_id}", response_model=DiscoveryStatusResponse)
def discovery_status(
    run_id: str,
    session: Session = Depends(get_db),
) -> DiscoveryStatusResponse:
    """Poll status of a discovery run.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    # In fixture mode, discovery completes immediately
    # Count entities in the database
    entity_count = session.query(TargetEntity).count()

    return DiscoveryStatusResponse(
        status="completed",
        entity_count=entity_count,
    )


class ResearchRequest(BaseModel):
    """Request to research a case."""
    case_id: str
    use_mock: bool = True


class ResearchResponse(BaseModel):
    """Response from research job submission."""
    job_id: str


@router.post("/research", response_model=ResearchResponse)
def start_research(
    req: ResearchRequest,
    session: Session = Depends(get_db),
) -> ResearchResponse:
    """Start research on a case with mock provider.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    case = session.query(EvaluationCase).filter_by(id=req.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case not found: {req.case_id}")

    # In fixture mode, create a placeholder job
    job_id = str(uuid4())

    # Real implementation would enqueue to RQ with mock provider
    # For now, just return the job ID

    return ResearchResponse(job_id=job_id)


class ResearchStatusResponse(BaseModel):
    """Status of a research job."""
    status: str  # completed, failed, pending
    error: Optional[str] = None


@router.get("/research-status/{job_id}", response_model=ResearchStatusResponse)
def research_status(
    job_id: str,
    session: Session = Depends(get_db),
) -> ResearchStatusResponse:
    """Poll status of a research job.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    # In fixture mode, research completes immediately
    return ResearchStatusResponse(status="completed")


class SimulateChangeRequest(BaseModel):
    """Request to simulate a change event."""
    watch_id: str


class SimulateChangeResponse(BaseModel):
    """Response from change simulation."""
    change_event_id: str


@router.post("/simulate-change", response_model=SimulateChangeResponse)
def simulate_change(
    req: SimulateChangeRequest,
    session: Session = Depends(get_db),
) -> SimulateChangeResponse:
    """Create a simulated change event for a watch.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    watch = session.query(WatchTarget).filter_by(id=req.watch_id).first()
    if not watch:
        raise HTTPException(status_code=404, detail=f"Watch not found: {req.watch_id}")

    # Create a change event
    now = datetime.now(timezone.utc)
    change_event = ChangeEvent(
        id=str(uuid4()),
        watch_id=watch.id,
        detected_at=now,
        source_url=watch.source_url or "http://example.com/simulated",
        fingerprint_old="old_hash",
        fingerprint_new="new_hash",
        diff_summary="Simulated change for testing",
    )
    session.add(change_event)
    session.commit()

    return SimulateChangeResponse(change_event_id=change_event.id)
