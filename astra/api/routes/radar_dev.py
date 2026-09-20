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

    from db.radar_models_evidence import SourceSnapshot

    watch = session.query(WatchTarget).filter_by(id=req.watch_id).first()
    if not watch:
        raise HTTPException(status_code=404, detail=f"Watch not found: {req.watch_id}")

    # Create a source snapshot for the watch
    snapshot = SourceSnapshot(
        source_url=watch.url,
        captured_at=datetime.now(timezone.utc),
        state="CAPTURED",
        fingerprint="old_hash",
    )
    session.add(snapshot)
    session.flush()

    # Create a watch check
    from db.radar_models_watch import WatchCheck
    check = WatchCheck(
        watch_target_id=watch.id,
        snapshot_id=snapshot.id,
        changed=True,
    )
    session.add(check)
    session.flush()

    # Create a change event
    now = datetime.now(timezone.utc)
    change_event = ChangeEvent(
        watch_check_id=check.id,
        summary="Simulated change for testing",
        material=True,
        at=now,
    )
    session.add(change_event)
    session.commit()

    return SimulateChangeResponse(change_event_id=change_event.id)


class ProfileResponse(BaseModel):
    """Response for profile with routes."""
    id: str
    name: Optional[str] = None
    routes: list[dict]


@router.get("/profile/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: str,
    session: Session = Depends(get_db),
) -> ProfileResponse:
    """Get profile with available routes.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    profile = session.query(CandidateProfile).filter_by(id=profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")

    routes = session.query(MozareRoute).all()
    routes_data = [{"id": r.id, "name": r.name} for r in routes]

    return ProfileResponse(
        id=profile.id,
        name=None,
        routes=routes_data
    )


class CaseListResponse(BaseModel):
    """Response for cases."""
    items: list[dict]


@router.get("/cases", response_model=CaseListResponse)
def list_cases_fixture(
    session: Session = Depends(get_db),
) -> CaseListResponse:
    """List evaluation cases in fixture mode.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    cases = session.query(EvaluationCase).all()
    items = [{"id": c.id, "research_state": c.research_state} for c in cases]

    return CaseListResponse(items=items)


class TargetListResponse(BaseModel):
    """Response for target entities."""
    items: list[dict]


@router.get("/targets", response_model=TargetListResponse)
def list_targets(
    session: Session = Depends(get_db),
) -> TargetListResponse:
    """List available target entities.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    targets = session.query(TargetEntity).all()
    items = [{"id": t.id, "kind": t.kind, "display_name": t.display_name} for t in targets]

    return TargetListResponse(items=items)


class CaseCreateRequest(BaseModel):
    """Request to create a case."""
    route_id: str
    target_id: str
    application_route: str


class CaseOutResponse(BaseModel):
    """Case response."""
    id: str
    research_state: str
    suggested_disposition: Optional[str]
    user_disposition: str
    blockers: list[dict] = Field(default_factory=list)
    unknown_count: int = 0
    deadline: Optional[dict] = None
    freshness: bool = True


@router.post("/cases", response_model=CaseOutResponse, status_code=201)
def create_case_fixture(
    req: CaseCreateRequest,
    session: Session = Depends(get_db),
) -> CaseOutResponse:
    """Create an evaluation case in fixture mode.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    from academic_radar.domain.enums import ApplicationRoute, ResearchState, UserDisposition, ApplicationStage

    try:
        ApplicationRoute(req.application_route)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid application_route: {req.application_route}")

    existing = session.query(EvaluationCase).filter(
        EvaluationCase.route_id == req.route_id,
        EvaluationCase.target_id == req.target_id,
        EvaluationCase.application_route == req.application_route,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Case already exists")

    case = EvaluationCase(
        route_id=req.route_id,
        target_id=req.target_id,
        application_route=req.application_route,
        research_state=ResearchState.DISCOVERED,
        user_disposition=UserDisposition.UNDECIDED,
        application_stage=ApplicationStage.NOT_STARTED,
    )
    session.add(case)
    session.commit()

    return CaseOutResponse(
        id=case.id,
        research_state=case.research_state,
        suggested_disposition=case.suggested_disposition,
        user_disposition=case.user_disposition,
        blockers=[],
        unknown_count=0,
        deadline=None,
        freshness=True
    )


class FundingCreateRequest(BaseModel):
    """Request to create funding assessment."""
    funding_route_id: str
    currency: str
    award_amount: Optional[str] = None
    tuition_amount: Optional[str] = None
    duration_months: Optional[int] = None
    known_costs: Optional[dict] = None
    unknown_costs: Optional[dict] = None
    uncovered_gap: Optional[str] = None
    state: str


class FundingResponse(BaseModel):
    """Funding assessment response."""
    id: str
    case_id: str
    funding_route_id: str
    currency: str
    award_amount: Optional[str] = None
    state: str


class WatchTargetCreateRequest(BaseModel):
    """Request to create a watch target."""
    case_id: str
    target_type: str
    check_interval_hours: int


class WatchTargetCreateResponse(BaseModel):
    """Watch target response."""
    id: str


@router.post("/watch-targets", response_model=WatchTargetCreateResponse, status_code=201)
def create_watch_target_fixture(
    req: WatchTargetCreateRequest,
    session: Session = Depends(get_db),
) -> WatchTargetCreateResponse:
    """Create a watch target in fixture mode.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    case = session.query(EvaluationCase).filter(EvaluationCase.id == req.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case not found")

    watch = WatchTarget(
        target_id=case.target_id,
        url="http://example.com/simulated",
        cadence="hourly",
    )
    session.add(watch)
    session.commit()

    return WatchTargetCreateResponse(
        id=watch.id,
    )


class BriefCreateRequest(BaseModel):
    """Request to create a brief."""
    case_id: str


class BriefCreateResponse(BaseModel):
    """Brief response."""
    id: str
    case_id: str


@router.post("/briefs", response_model=BriefCreateResponse, status_code=201)
def create_brief_fixture(
    req: BriefCreateRequest,
    session: Session = Depends(get_db),
) -> BriefCreateResponse:
    """Create an application brief in fixture mode.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    case = session.query(EvaluationCase).filter(EvaluationCase.id == req.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    brief = ApplicationBrief(
        case_id=req.case_id,
        state="DRAFT",
    )
    session.add(brief)
    session.commit()

    return BriefCreateResponse(
        id=brief.id,
        case_id=brief.case_id,
    )


@router.post("/funding/{case_id}", response_model=FundingResponse, status_code=201)
def create_funding_fixture(
    case_id: str,
    req: FundingCreateRequest,
    session: Session = Depends(get_db),
) -> FundingResponse:
    """Create a funding assessment in fixture mode.

    Creates a FundingRoute target entity if needed.
    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    from decimal import Decimal
    from db.radar_models_claims import FundingAssessment

    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Check if the funding_route_id exists as a TargetEntity; if not, create it
    funding_target = session.query(TargetEntity).filter(
        TargetEntity.id == req.funding_route_id
    ).first()

    if not funding_target:
        funding_target = TargetEntity(
            id=req.funding_route_id,
            kind="FundingRoute",
            display_name=req.funding_route_id,
            source_authority="DISCOVERY_AGGREGATOR",
        )
        session.add(funding_target)
        session.flush()

    award_amount = Decimal(req.award_amount) if req.award_amount else None

    assessment = FundingAssessment(
        case_id=case_id,
        funding_route_id=req.funding_route_id,
        currency=req.currency,
        award_amount=award_amount,
        tuition_amount=Decimal(req.tuition_amount) if req.tuition_amount else None,
        duration_months=req.duration_months,
        known_costs=req.known_costs,
        unknown_costs=req.unknown_costs,
        uncovered_gap=Decimal(req.uncovered_gap) if req.uncovered_gap else None,
        state=req.state,
    )
    session.add(assessment)
    session.commit()

    return FundingResponse(
        id=assessment.id,
        case_id=assessment.case_id,
        funding_route_id=assessment.funding_route_id,
        currency=assessment.currency,
        award_amount=str(award_amount) if award_amount else None,
        state=assessment.state,
    )
