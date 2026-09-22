"""api.routes.radar_misc — Radar misc API endpoints.

Implements GET/POST /funding/{case_id}, GET/POST /watch/targets,
GET /watch/changes, GET /routes, POST /routes, PATCH /routes/{id},
PATCH /routes/{id}/state, GET /profile, PUT /profile.
"""

from __future__ import annotations

from typing import Any, Optional
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
    """Route response model.

    ``operations_methods``, ``relevant_corpora_material``, ``target_disciplines``
    and ``prohibited_overclaims`` are stored as JSON lists of plain strings (see
    ``academic_radar.profile.mozare_import``), not dicts — ``Any`` here so both
    the real list shape and any legacy/dict fixture data validate.
    """
    id: str
    name: str
    state: str
    route_statement: Optional[str] = None
    core_problem: Optional[str] = None
    operations_methods: Optional[Any] = None
    relevant_corpora_material: Optional[Any] = None
    supporting_evidence: Optional[Any] = None
    target_disciplines: Optional[Any] = None
    prohibited_overclaims: Optional[Any] = None
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


class RouteCreateIn(BaseModel):
    """Request body for creating a research route.

    Mirrors the fields a real route needs to be usable by discovery/matching
    (see ``academic_radar.profile.mozare_import._import_route``); free-form
    lists (methods, corpora, disciplines, overclaims) are plain strings.
    """
    name: str
    state: str = "ACTIVE"
    route_statement: Optional[str] = None
    core_problem: Optional[str] = None
    operations_methods: Optional[list[str]] = None
    relevant_corpora_material: Optional[list[str]] = None
    target_disciplines: Optional[list[str]] = None
    prohibited_overclaims: Optional[list[str]] = None
    maturity: Optional[str] = None


class RouteUpdateIn(BaseModel):
    """Request body for editing a research route's fields.

    All fields optional (partial update); state transitions are validated the
    same way as ``PATCH /routes/{id}/state`` when included here too, since the
    edit form lets a user retire/reactivate a route from the same save.
    """
    name: Optional[str] = None
    state: Optional[str] = None
    route_statement: Optional[str] = None
    core_problem: Optional[str] = None
    operations_methods: Optional[list[str]] = None
    relevant_corpora_material: Optional[list[str]] = None
    target_disciplines: Optional[list[str]] = None
    prohibited_overclaims: Optional[list[str]] = None
    maturity: Optional[str] = None


@router.get("/routes", response_model=RouteListResponse)
def list_routes(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> RouteListResponse:
    """List all MozareRoutes."""
    routes = session.query(MozareRoute).all()
    items = [RouteOut.model_validate(r, from_attributes=True) for r in routes]
    return RouteListResponse(items=items)


@router.post("/routes", response_model=RouteOut, status_code=201)
def create_route(
    body: RouteCreateIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> RouteOut:
    """Create a new research route (MozareRoute).

    Lets the owner add a research direction from the profile form, without
    going through the dev-only fixture seed importer.
    """
    try:
        RouteState(body.state)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid state: {body.state}")

    route = MozareRoute(
        name=body.name,
        state=body.state,
        route_statement=body.route_statement,
        core_problem=body.core_problem,
        operations_methods=body.operations_methods,
        relevant_corpora_material=body.relevant_corpora_material,
        target_disciplines=body.target_disciplines,
        prohibited_overclaims=body.prohibited_overclaims,
        maturity=body.maturity,
    )
    session.add(route)
    session.commit()

    return RouteOut.model_validate(route, from_attributes=True)


@router.patch("/routes/{route_id}", response_model=RouteOut)
def update_route(
    route_id: str,
    body: RouteUpdateIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> RouteOut:
    """Edit a research route's fields (partial update; unset fields are left alone)."""
    route = session.query(MozareRoute).filter(MozareRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")

    data = body.model_dump(exclude_unset=True)
    if "state" in data:
        try:
            RouteState(data["state"])
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid state: {data['state']}")

    for field, value in data.items():
        setattr(route, field, value)
    session.commit()

    return RouteOut.model_validate(route, from_attributes=True)


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
    """Candidate profile response model.

    ``education``, ``language_evidence``, ``scholarly_work``,
    ``artistic_curatorial_work`` and ``professional_technical_evidence`` are
    each stored as a JSON list of fact dicts (see
    ``academic_radar.profile.mozare_import``), each carrying its own
    ``provenance`` — ``Any`` here so both that real list shape and any
    legacy/dict fixture data validate.
    """
    id: str
    state: str
    fixed_constraints: Optional[str] = None
    education: Optional[Any] = None
    language_evidence: Optional[Any] = None
    scholarly_work: Optional[Any] = None
    artistic_curatorial_work: Optional[Any] = None
    professional_technical_evidence: Optional[Any] = None
    verification_status: Optional[str] = None
    documents: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# A human filling out the profile form supplies fact fields only (e.g.
# {"degree": "MSc Physics", "institution": "..."}); provenance is not
# something a non-technical user can meaningfully declare by hand, so the
# server stamps every fact with a fixed self-reported/unverified provenance,
# matching the {source, verified} shape the dev seed importer enforces
# (academic_radar.profile.mozare_import._validate_provenance).
SELF_REPORTED_PROVENANCE = {
    "source": "Self-reported via profile form",
    "verified": False,
}


def _with_self_reported_provenance(
    items: Optional[list[dict[str, Any]]],
) -> Optional[list[dict[str, Any]]]:
    """Attach the default provenance to every fact in a list, dropping any
    client-supplied ``provenance`` so a user can never mark their own facts
    as independently verified."""
    if not items:
        return None
    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=422, detail="Each fact must be an object of field/value pairs"
            )
        fact = {k: v for k, v in item.items() if k != "provenance"}
        fact["provenance"] = dict(SELF_REPORTED_PROVENANCE)
        normalized.append(fact)
    return normalized


class ProfileUpdateIn(BaseModel):
    """Request body for creating/updating the candidate profile.

    Only the fact fields are accepted — provenance is never supplied by the
    client (see ``_with_self_reported_provenance``). Any section omitted
    (left as ``None``) is left unchanged; pass an empty list to clear a
    section.
    """
    fixed_constraints: Optional[str] = None
    education: Optional[list[dict[str, Any]]] = None
    language_evidence: Optional[list[dict[str, Any]]] = None
    scholarly_work: Optional[list[dict[str, Any]]] = None
    artistic_curatorial_work: Optional[list[dict[str, Any]]] = None
    professional_technical_evidence: Optional[list[dict[str, Any]]] = None


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


@router.put("/profile", response_model=ProfileOut)
def upsert_profile(
    body: ProfileUpdateIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ProfileOut:
    """Create the candidate profile if none exists yet, or update the active one.

    Academic Radar is a single-owner workspace (RADAR_OWNER_EMAIL), so there
    is exactly one profile to upsert: the current ACTIVE row, or a fresh one
    if this is the first save. Fields left out of the request body (None) are
    left unchanged; send an empty list to clear a section.
    """
    profile = session.query(CandidateProfile).filter(
        CandidateProfile.state == "ACTIVE"
    ).first()
    if profile is None:
        profile = CandidateProfile(state="ACTIVE")
        session.add(profile)

    body_data = body.model_dump(exclude_unset=True)
    if "fixed_constraints" in body_data:
        profile.fixed_constraints = body.fixed_constraints
    if "education" in body_data:
        profile.education = _with_self_reported_provenance(body.education)
    if "language_evidence" in body_data:
        profile.language_evidence = _with_self_reported_provenance(body.language_evidence)
    if "scholarly_work" in body_data:
        profile.scholarly_work = _with_self_reported_provenance(body.scholarly_work)
    if "artistic_curatorial_work" in body_data:
        profile.artistic_curatorial_work = _with_self_reported_provenance(body.artistic_curatorial_work)
    if "professional_technical_evidence" in body_data:
        profile.professional_technical_evidence = _with_self_reported_provenance(body.professional_technical_evidence)

    session.commit()
    session.refresh(profile)

    return ProfileOut.model_validate(profile, from_attributes=True)
