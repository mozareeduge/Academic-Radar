"""api.routes.radar_cases — Radar evaluation cases API endpoints.

Implements GET /cases, GET /cases/{id}, POST /cases, POST /cases/{id}/disposition,
POST /cases/{id}/notes, POST /cases/{id}/stage with explicit response models.
"""

from __future__ import annotations

import os
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User
from db.radar_models_cases import EvaluationCase, UserNotes, ApplicationStageHistory
from academic_radar.domain import disposition as dsp
from academic_radar.domain.enums import UserDisposition, ApplicationRoute, ApplicationStage, ResearchState
from academic_radar.domain.case_truth import case_truth
from academic_radar.research.protocol_loader import load_protocols

router = APIRouter(prefix="/api/radar", tags=["radar"])


class DeadlineOut(BaseModel):
    """Deadline representation."""
    original_text: Optional[str] = None
    precision: Optional[str] = None


class CaseOut(BaseModel):
    """Case response model."""
    id: str
    research_state: str
    suggested_disposition: Optional[str]
    user_disposition: str
    blockers: list[dict] = Field(default_factory=list)
    unknown_count: int = 0
    deadline: Optional[DeadlineOut] = None
    freshness: Optional[bool] = None
    brief_block_reasons: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    """List response for cases."""
    items: list[CaseOut]


class CaseCreateIn(BaseModel):
    """Request body for creating a case."""
    route_id: str
    target_id: str
    application_route: str


@router.post("/cases", response_model=CaseOut, status_code=201)
def create_case(
    body: CaseCreateIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CaseOut:
    """Create a new evaluation case.

    Args:
        body.route_id: MozareRoute ID
        body.target_id: TargetEntity ID
        body.application_route: ApplicationRoute enum value

    Returns:
        201 with case data

    Raises:
        409 if (route_id, target_id, application_route) already exists
        422 if application_route is invalid
    """
    try:
        ApplicationRoute(body.application_route)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid application_route: {body.application_route}")

    existing = session.query(EvaluationCase).filter(
        EvaluationCase.route_id == body.route_id,
        EvaluationCase.target_id == body.target_id,
        EvaluationCase.application_route == body.application_route,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Case already exists for this route, target, and application_route")

    case = EvaluationCase(
        route_id=body.route_id,
        target_id=body.target_id,
        application_route=body.application_route,
        research_state=ResearchState.DISCOVERED,
        user_disposition=UserDisposition.UNDECIDED,
        application_stage=ApplicationStage.NOT_STARTED,
    )
    session.add(case)
    session.commit()

    return _case_to_out(session, case)


@router.get("/cases", response_model=CaseListResponse)
def list_cases(
    application_route: Optional[str] = Query(None),
    research_state: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CaseListResponse:
    """List evaluation cases with optional filters.

    Filters:
    - application_route: Filter by application route type
    - research_state: Filter by research state

    Returns each case with:
    - ids, research_state, suggested_disposition, user_disposition
    - blockers, unknown_count, deadline (with original_text and precision)
    - freshness flag
    """
    stmt = select(EvaluationCase)

    if application_route:
        stmt = stmt.where(EvaluationCase.application_route == application_route)

    if research_state:
        stmt = stmt.where(EvaluationCase.research_state == research_state)

    cases = session.scalars(stmt).all()

    items = [_case_to_out(session, c) for c in cases]
    return CaseListResponse(items=items)


@router.get("/cases/{case_id}", response_model=CaseOut)
def get_case(
    case_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CaseOut:
    """Get a single case by ID."""
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    return _case_to_out(session, case)


class DispositionIn(BaseModel):
    """Request body for setting disposition."""
    value: str
    reason: Optional[str] = None


@router.post("/cases/{case_id}/disposition", response_model=CaseOut)
def set_disposition(
    case_id: str,
    body: DispositionIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CaseOut:
    """Set user disposition on a case.

    Calls domain.disposition.set_user_disposition with actor 'USER'.

    Args:
        case_id: The case ID
        body.value: New disposition (UNDECIDED, STRONG, WATCH, ACT, REJECTED)
        body.reason: Optional reason for the change
    """
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Validate the disposition value
    try:
        UserDisposition(body.value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid disposition value: {body.value}")

    dsp.set_user_disposition(
        session,
        case_id,
        body.value,
        actor="USER",
        reason=body.reason or ""
    )
    session.commit()

    return _case_to_out(session, case)


class NoteIn(BaseModel):
    """Request body for creating a note."""
    body: str


@router.post("/cases/{case_id}/notes", status_code=201)
def post_note(
    case_id: str,
    body: NoteIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict:
    """Create a note on a case."""
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    note = UserNotes(case_id=case_id, body=body.body)
    session.add(note)
    session.commit()

    return {"status": "ok"}


class StageIn(BaseModel):
    """Request body for updating application stage."""
    stage: str


@router.post("/cases/{case_id}/stage", response_model=CaseOut)
def post_stage(
    case_id: str,
    body: StageIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CaseOut:
    """Update application stage on a case."""
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    previous = case.application_stage
    case.application_stage = body.stage
    session.flush()

    history = ApplicationStageHistory(
        case_id=case_id,
        previous=previous,
        new=body.stage
    )
    session.add(history)
    session.commit()

    return _case_to_out(session, case)


def _case_to_out(session: Session, case: EvaluationCase) -> CaseOut:
    """Convert EvaluationCase model to response output."""
    truth = case_truth(session, case, load_protocols()[case.application_route])
    return CaseOut(
        id=case.id,
        research_state=case.research_state,
        suggested_disposition=case.suggested_disposition,
        user_disposition=case.user_disposition,
        blockers=truth.blockers,
        unknown_count=truth.unknown_count,
        deadline=truth.deadline,
        freshness=truth.freshness,
        brief_block_reasons=truth.brief_block_reasons,
    )
