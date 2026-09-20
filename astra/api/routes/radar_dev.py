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

    Requires RADAR_FIXTURE_MODE=1. Runs inline and returns the run_id.
    """
    _fixture_mode_only()

    case = session.query(EvaluationCase).filter_by(id=req.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case not found: {req.case_id}")

    import sys
    print(f"DEBUG: /research endpoint called for case {req.case_id}", file=sys.stderr, flush=True)

    from academic_radar.research.service import run_research
    from academic_radar.research.fixtures import fixture_evidence_and_provider

    # Set up fixture provider and evidence
    try:
        provider, evidence_lookup = fixture_evidence_and_provider(session, case)
        print(f"DEBUG: fixture_evidence_and_provider completed, got {len(evidence_lookup)} evidence items", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"DEBUG: fixture_evidence_and_provider failed: {e}", file=sys.stderr, flush=True)
        raise HTTPException(status_code=400, detail=f"Fixture setup failed: {str(e)}")

    # Run research inline
    try:
        run_id = run_research(session, req.case_id, provider, evidence_lookup)
        print(f"DEBUG: run_research completed, got run_id {run_id}", file=sys.stderr, flush=True)
        return ResearchResponse(job_id=run_id)
    except Exception as e:
        print(f"DEBUG: run_research failed: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=400, detail=f"Research failed: {str(e)}")


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

    Requires RADAR_FIXTURE_MODE=1. Reads real run row from database.
    """
    _fixture_mode_only()

    from db.radar_models_evidence import ResearchRun

    run = session.query(ResearchRun).filter_by(id=job_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {job_id}")

    status_map = {
        "QUEUED": "pending",
        "RUNNING": "pending",
        "COMPLETED": "completed",
        "PARTIAL": "completed",
        "FAILED": "failed",
    }
    status = status_map.get(run.status, "pending")

    return ResearchStatusResponse(status=status)


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
    tuition: Optional[str] = None
    tuition_amount: Optional[str] = None
    living_costs: Optional[str] = None
    mandatory_fees: Optional[str] = None
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
    source_url: Optional[str] = None


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


class GateCreateRequest(BaseModel):
    """Request to create a gate assessment."""
    requirement: str
    result: str
    evidence_ids: Optional[list[str]] = None


class GateCreateResponse(BaseModel):
    """Gate assessment response."""
    id: str
    case_id: str
    requirement: str
    result: str


@router.post("/gate/{case_id}", response_model=GateCreateResponse, status_code=201)
def create_gate_fixture(
    case_id: str,
    req: GateCreateRequest,
    session: Session = Depends(get_db),
) -> GateCreateResponse:
    """Create a gate assessment in fixture mode.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    from db.radar_models_claims import GateAssessment

    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    gate = GateAssessment(
        case_id=case_id,
        requirement=req.requirement,
        source_authority="OFFICIAL_REGULATION",
        result=req.result,
        evidence_ids=req.evidence_ids or [],
    )
    session.add(gate)
    session.commit()

    return GateCreateResponse(
        id=gate.id,
        case_id=gate.case_id,
        requirement=gate.requirement,
        result=gate.result,
    )


class WatchRunRequest(BaseModel):
    """Request to run a watch check and trigger invalidation."""
    case_id: str
    source_url: str
    prior_text: str
    changed_text: str


class WatchRunResponse(BaseModel):
    """Response from watch run."""
    change_event_id: Optional[str] = None


@router.post("/watch-run", response_model=WatchRunResponse, status_code=200)
def run_watch_and_invalidate_fixture(
    req: WatchRunRequest,
    session: Session = Depends(get_db),
) -> WatchRunResponse:
    """Run a real watch check, record change event, and invalidate dependent objects.

    Implements the real flow: fetch -> snapshot -> change event -> invalidate.
    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    from academic_radar.watch.checks import run_watch_check
    from academic_radar.domain.invalidation import invalidate

    from db.radar_models_evidence import SourceSnapshot

    case = session.query(EvaluationCase).filter(EvaluationCase.id == req.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {req.case_id} not found")

    # Create initial snapshot with prior text (if not already present)
    from academic_radar.evidence.snapshots import record_snapshot as rec_snap
    initial_snap = session.query(SourceSnapshot).filter_by(source_url=req.source_url).first()
    if not initial_snap:
        initial_snap = rec_snap(session, req.source_url, req.prior_text, True)
        session.flush()

    # Create/find watch target for this URL
    watch = session.query(WatchTarget).filter(WatchTarget.url == req.source_url).first()
    if not watch:
        watch = WatchTarget(
            target_id=case.target_id,
            url=req.source_url,
            cadence="daily",
        )
        session.add(watch)
        session.flush()

    # Mock fetch function that returns the changed text
    def mock_fetch(url: str):
        if url == req.source_url:
            return (req.changed_text, True)
        return (None, False)

    # Run watch check with prior text
    result = run_watch_check(
        session, {"id": watch.id, "url": watch.url}, mock_fetch,
        prior_text=req.prior_text
    )

    # If snapshot changed, invalidate dependent objects
    # Invalidate the INITIAL snapshot (which has the dependency link), not the new one
    if result["snapshot_state"] == "CHANGED":
        invalidate(session, initial_snap.id)

    session.commit()

    change_event_id = result.get("change_event_id") or result.get("snapshot_id")
    return WatchRunResponse(change_event_id=change_event_id)


@router.post("/briefs", response_model=BriefCreateResponse, status_code=201)
def create_brief_fixture(
    req: BriefCreateRequest,
    session: Session = Depends(get_db),
) -> BriefCreateResponse:
    """Create an application brief in fixture mode using real freeze_brief logic.

    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    from academic_radar.domain.briefs import freeze_brief, BriefBlocked

    case = session.query(EvaluationCase).filter(EvaluationCase.id == req.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {req.case_id} not found")

    try:
        brief_id = freeze_brief(session, req.case_id)
    except BriefBlocked as e:
        raise HTTPException(status_code=422, detail=f"Brief blocked: {'; '.join(e.reasons)}")

    session.commit()

    return BriefCreateResponse(
        id=brief_id,
        case_id=req.case_id,
    )


@router.post("/funding/{case_id}", response_model=FundingResponse, status_code=201)
def create_funding_fixture(
    case_id: str,
    req: FundingCreateRequest,
    session: Session = Depends(get_db),
) -> FundingResponse:
    """Create a funding assessment in fixture mode using real compute_gap logic.

    Creates a FundingRoute target entity and evidence artifacts as needed.
    Persists via real code path using domain.funding.compute_gap.
    Requires RADAR_FIXTURE_MODE=1.
    """
    _fixture_mode_only()

    from decimal import Decimal
    from uuid import uuid4
    from academic_radar.domain.funding import compute_gap, FundingInputs, fully_funded_label_allowed
    from academic_radar.domain.invalidation import add_dependency
    from academic_radar.evidence.snapshots import record_snapshot
    from academic_radar.evidence.artifacts import create_artifact
    from db.radar_models_claims import FundingAssessment, Claim, ClaimEvidence
    from db.radar_models_evidence import EvidenceArtifact

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
    tuition = Decimal(req.tuition) if req.tuition else (Decimal(req.known_costs.get("tuition")) if req.known_costs and "tuition" in req.known_costs else None)
    living_costs = Decimal(req.living_costs) if req.living_costs else (Decimal(req.known_costs.get("living_costs")) if req.known_costs and "living_costs" in req.known_costs else None)
    mandatory_fees = Decimal(req.mandatory_fees) if req.mandatory_fees else (Decimal(req.known_costs.get("mandatory_fees")) if req.known_costs and "mandatory_fees" in req.known_costs else None)

    # Create funding evidence snapshot and artifact
    funding_url = f"https://fixtures.example.org/funding/{case_id}/{req.funding_route_id}"
    snapshot = record_snapshot(session, funding_url, f"Funding data for {req.funding_route_id}", True)
    now = datetime.now(timezone.utc)
    artifact = create_artifact(
        session, snapshot, funding_url, "text/plain",
        f"Fixture funding for {req.funding_route_id}",
        now.isoformat() if isinstance(now, datetime) else now
    )
    session.flush()

    # Compute gap using real logic
    unknown_items = []
    if req.unknown_costs:
        unknown_items = list(req.unknown_costs.keys())

    inputs = FundingInputs(
        currency=req.currency,
        annual_award=award_amount,
        fee_waiver=Decimal("0"),
        reliable_external=Decimal("0"),
        tuition=tuition,
        mandatory_fees=mandatory_fees,
        living_costs=living_costs,
        insurance_visa_relocation=Decimal("0"),
        duration_months=req.duration_months or 12,
        unknown_cost_items=unknown_items,
    )
    result = compute_gap(inputs)

    # Determine if "fully funded" label is allowed
    is_fully_funded = fully_funded_label_allowed(result)

    # Create funding assessment with computed gap
    assessment = FundingAssessment(
        case_id=case_id,
        funding_route_id=req.funding_route_id,
        currency=req.currency,
        award_amount=award_amount,
        tuition_amount=tuition,
        duration_months=req.duration_months,
        known_costs=req.known_costs or {},
        unknown_costs=req.unknown_costs or {},
        uncovered_gap=result.annual_gap_or_surplus,
        state=req.state,
    )
    session.add(assessment)
    session.flush()

    # Create backing claim and link evidence
    claim = Claim(
        case_id=case_id,
        statement=f"Funding assessment for {req.funding_route_id}",
        claim_type="EXTERNAL_FACT",
        status="SUPPORTED" if result.complete else "UNKNOWN",
    )
    session.add(claim)
    session.flush()

    ce = ClaimEvidence(claim_id=claim.id, evidence_artifact_id=artifact.id)
    session.add(ce)
    session.flush()

    # Link evidence snapshot to the case (funding assessments are details of the case)
    # This way when funding evidence changes, the case becomes STALE
    add_dependency(session, "SourceSnapshot", snapshot.id, "EvaluationCase", case_id)

    session.commit()

    return FundingResponse(
        id=assessment.id,
        case_id=assessment.case_id,
        funding_route_id=assessment.funding_route_id,
        currency=assessment.currency,
        award_amount=str(award_amount) if award_amount else None,
        state=assessment.state,
        source_url=funding_url,
    )
