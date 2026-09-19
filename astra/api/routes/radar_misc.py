"""api.routes.radar_misc — Radar misc API endpoints.

Implements GET/POST /funding/{case_id}, GET/POST /watch/targets,
GET /watch/changes, GET /routes, PATCH /routes/{id}/state, GET /profile.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User
from db.radar_models_cases import EvaluationCase
from db.radar_models_targets import MozareRoute, CandidateProfile, TargetEntity
from db.radar_models_claims import FundingAssessment
from db.radar_models_watch import WatchTarget, ChangeEvent, WatchCheck
from academic_radar.domain.enums import RouteState, WatchTargetState, FundingAssessmentState
from academic_radar.domain import funding as funding_module
from academic_radar.domain import invalidation

router = APIRouter(prefix="/api/radar", tags=["radar"])


# ============================================================================
# Funding Endpoints
# ============================================================================

class FundingAssessmentOut(BaseModel):
    """Funding assessment response model with string serialization for Decimal."""
    id: str
    case_id: str
    funding_route_id: str
    currency: str
    award_amount: Optional[str] = None
    tuition_amount: Optional[str] = None
    duration_months: Optional[int] = None
    known_costs: Optional[dict] = None
    unknown_costs: Optional[dict] = None
    uncovered_gap: Optional[str] = None
    state: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_db(cls, obj: FundingAssessment) -> FundingAssessmentOut:
        """Convert DB model to response, serializing Decimal amounts as strings."""
        return cls(
            id=obj.id,
            case_id=obj.case_id,
            funding_route_id=obj.funding_route_id,
            currency=obj.currency,
            award_amount=str(obj.award_amount) if obj.award_amount is not None else None,
            tuition_amount=str(obj.tuition_amount) if obj.tuition_amount is not None else None,
            duration_months=obj.duration_months,
            known_costs=obj.known_costs,
            unknown_costs=obj.unknown_costs,
            uncovered_gap=str(obj.uncovered_gap) if obj.uncovered_gap is not None else None,
            state=obj.state,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class FundingListResponse(BaseModel):
    """List response for funding assessments."""
    items: list[FundingAssessmentOut]


class FundingCreateIn(BaseModel):
    """Request body for creating a funding assessment."""
    funding_route_id: str
    currency: str
    award_amount: Optional[str] = None
    tuition_amount: Optional[str] = None
    duration_months: Optional[int] = None
    known_costs: Optional[dict] = None
    unknown_costs: Optional[dict] = None
    uncovered_gap: Optional[str] = None
    state: str


@router.get("/funding/{case_id}", response_model=FundingListResponse)
def list_funding(
    case_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> FundingListResponse:
    """List funding assessments for a case.

    All Decimal amounts (award_amount, tuition_amount, uncovered_gap) are
    serialized as strings to preserve precision and avoid floating-point errors.
    """
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    assessments = session.query(FundingAssessment).filter(
        FundingAssessment.case_id == case_id
    ).all()

    items = [FundingAssessmentOut.from_db(a) for a in assessments]
    return FundingListResponse(items=items)


@router.post("/funding/{case_id}", response_model=FundingAssessmentOut, status_code=201)
def create_funding(
    case_id: str,
    body: FundingCreateIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> FundingAssessmentOut:
    """Create a new funding assessment for a case.

    Amounts in request body are strings; they are converted to Decimal in the DB.
    Response serializes amounts back to strings for precision.
    """
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Convert string amounts to Decimal
    award_amount = Decimal(body.award_amount) if body.award_amount else None
    tuition_amount = Decimal(body.tuition_amount) if body.tuition_amount else None
    uncovered_gap = Decimal(body.uncovered_gap) if body.uncovered_gap else None

    # Validate state
    try:
        FundingAssessmentState(body.state)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid state: {body.state}")

    assessment = FundingAssessment(
        case_id=case_id,
        funding_route_id=body.funding_route_id,
        currency=body.currency,
        award_amount=award_amount,
        tuition_amount=tuition_amount,
        duration_months=body.duration_months,
        known_costs=body.known_costs,
        unknown_costs=body.unknown_costs,
        uncovered_gap=uncovered_gap,
        state=body.state,
    )
    session.add(assessment)
    session.commit()

    return FundingAssessmentOut.from_db(assessment)


# ============================================================================
# Watch Endpoints
# ============================================================================

class WatchTargetOut(BaseModel):
    """Watch target response model."""
    id: str
    target_id: str
    url: str
    cadence: str
    state: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchTargetListResponse(BaseModel):
    """List response for watch targets."""
    items: list[WatchTargetOut]


class WatchTargetCreateIn(BaseModel):
    """Request body for creating a watch target."""
    target_id: str
    url: str
    cadence: str
    state: str = "ACTIVE"


@router.get("/watch/targets", response_model=WatchTargetListResponse)
def list_watch_targets(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> WatchTargetListResponse:
    """List all watch targets."""
    targets = session.query(WatchTarget).all()
    items = [WatchTargetOut.model_validate(t, from_attributes=True) for t in targets]
    return WatchTargetListResponse(items=items)


@router.post("/watch/targets", response_model=WatchTargetOut, status_code=201)
def create_watch_target(
    body: WatchTargetCreateIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> WatchTargetOut:
    """Create a new watch target."""
    # Validate state
    try:
        WatchTargetState(body.state)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid state: {body.state}")

    target = WatchTarget(
        target_id=body.target_id,
        url=body.url,
        cadence=body.cadence,
        state=body.state,
    )
    session.add(target)
    session.commit()

    return WatchTargetOut.model_validate(target, from_attributes=True)


class ChangeEventOut(BaseModel):
    """Change event response model with impacted cases."""
    id: str
    watch_check_id: str
    summary: str
    material: bool
    at: datetime
    impacted_cases: list[str]

    model_config = ConfigDict(from_attributes=True)


class ChangeEventsListResponse(BaseModel):
    """List response for change events."""
    items: list[ChangeEventOut]


@router.get("/watch/changes", response_model=ChangeEventsListResponse)
def list_change_events(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ChangeEventsListResponse:
    """List change events with impacted cases from invalidation report.

    For each change event, queries the invalidation graph to find which cases
    would be impacted if that snapshot were marked changed.
    """
    events = session.query(ChangeEvent).all()
    items = []

    for event in events:
        # Get the watch check to find the snapshot
        check = session.query(WatchCheck).filter(
            WatchCheck.id == event.watch_check_id
        ).first()

        impacted_cases = []
        if check:
            # Run invalidation on the snapshot to see what cases would be affected
            report = invalidation.invalidate(session, check.snapshot_id)
            impacted_cases = report.stale_cases
            # Rollback the invalidation changes since this is just a query
            session.rollback()

        items.append(ChangeEventOut(
            id=event.id,
            watch_check_id=event.watch_check_id,
            summary=event.summary,
            material=event.material,
            at=event.at,
            impacted_cases=impacted_cases,
        ))

    return ChangeEventsListResponse(items=items)


# ============================================================================
# Routes Endpoints
# ============================================================================

class RouteOut(BaseModel):
    """Route response model."""
    id: str
    name: str
    state: str
    route_statement: Optional[str] = None
    core_problem: Optional[str] = None
    operations_methods: Optional[dict] = None
    relevant_corpora_material: Optional[dict] = None
    supporting_evidence: Optional[dict] = None
    target_disciplines: Optional[dict] = None
    prohibited_overclaims: Optional[dict] = None
    maturity: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RouteListResponse(BaseModel):
    """List response for routes."""
    items: list[RouteOut]


class RouteStatePatchIn(BaseModel):
    """Request body for updating route state."""
    state: str


@router.get("/routes", response_model=RouteListResponse)
def list_routes(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> RouteListResponse:
    """List all MozareRoutes."""
    routes = session.query(MozareRoute).all()
    items = [RouteOut.model_validate(r, from_attributes=True) for r in routes]
    return RouteListResponse(items=items)


@router.patch("/routes/{route_id}/state", response_model=RouteOut)
def update_route_state(
    route_id: str,
    body: RouteStatePatchIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> RouteOut:
    """Update the state of a route.

    Validates that the new state is a valid RouteState enum value.
    """
    route = session.query(MozareRoute).filter(MozareRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")

    # Validate state
    try:
        RouteState(body.state)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid state: {body.state}")

    route.state = body.state
    session.commit()

    return RouteOut.model_validate(route, from_attributes=True)


# ============================================================================
# Profile Endpoint
# ============================================================================

class ProfileOut(BaseModel):
    """Candidate profile response model."""
    id: str
    state: str
    fixed_constraints: Optional[str] = None
    education: Optional[dict] = None
    language_evidence: Optional[dict] = None
    scholarly_work: Optional[dict] = None
    artistic_curatorial_work: Optional[dict] = None
    professional_technical_evidence: Optional[dict] = None
    verification_status: Optional[str] = None
    documents: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/profile", response_model=ProfileOut)
def get_profile(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ProfileOut:
    """Get the active candidate profile.

    Returns the first ACTIVE profile found, or 404 if none exists.
    """
    profile = session.query(CandidateProfile).filter(
        CandidateProfile.state == "ACTIVE"
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="No active profile found")

    return ProfileOut.model_validate(profile, from_attributes=True)
