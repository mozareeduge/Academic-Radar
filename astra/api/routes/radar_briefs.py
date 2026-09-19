"""api.routes.radar_briefs — Radar application brief endpoints.

Implements POST /api/radar/cases/{id}/brief (freeze brief via domain.briefs)
and GET /api/radar/briefs/{id} (retrieve brief with superseded flag).

FLOW-009: Application preparation → freeze brief → downstream writing/outreach.
No auto-send or email functionality.
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User
from db.radar_models_watch import ApplicationBrief
from academic_radar.domain.briefs import freeze_brief, is_superseded, BriefBlocked

router = APIRouter(prefix="/api/radar", tags=["radar"])


class BriefBlockedOut(BaseModel):
    """Response when brief cannot be frozen."""
    detail: str
    reasons: list[str]


class BriefFrozenOut(BaseModel):
    """Response after successfully freezing a brief."""
    id: str
    case_id: str
    frozen_at: datetime
    state: str

    model_config = ConfigDict(from_attributes=True)


class BriefContentStatement(BaseModel):
    """A statement in the brief with evidence links."""
    statement: str
    evidence_count: int
    freshness: str


class BriefOut(BaseModel):
    """Complete brief with content and superseded status."""
    id: str
    case_id: str
    frozen_at: Optional[datetime]
    state: str
    superseded: bool
    content: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/cases/{case_id}/brief", response_model=BriefFrozenOut)
def freeze_brief_endpoint(
    case_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> BriefFrozenOut:
    """Freeze an application brief from the current case state.

    Builds content from current claims/gates/dimensions/funding where EVERY
    statement carries evidence ids and source freshness. Returns 409 Conflict
    if any critical fact is STALE or any hard gate is UNKNOWN.

    Args:
        case_id: ID of the evaluation case to freeze.

    Returns:
        Newly created brief with id, case_id, frozen_at, state.

    Raises:
        404: Case not found.
        409: Conflict — brief cannot be frozen due to stale/unknown facts.
    """
    try:
        brief_id = freeze_brief(session, case_id)
        brief = session.query(ApplicationBrief).filter(ApplicationBrief.id == brief_id).one()
        session.commit()
        return BriefFrozenOut.model_validate(brief)
    except BriefBlocked as e:
        raise HTTPException(
            status_code=409,
            detail="Brief cannot be frozen: stale or unknown critical facts",
            headers={"X-Brief-Blocked-Reasons": "; ".join(e.reasons)},
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/briefs/{brief_id}", response_model=BriefOut)
def get_brief(
    brief_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> BriefOut:
    """Get a brief by ID with superseded status.

    Retrieves the brief and checks if it has been superseded by dependency
    changes (snapshot fingerprint changed or missing).

    Args:
        brief_id: ID of the brief to retrieve.

    Returns:
        Brief with id, case_id, frozen_at, state, superseded, content.

    Raises:
        404: Brief not found.
    """
    brief = session.query(ApplicationBrief).filter(ApplicationBrief.id == brief_id).one_or_none()
    if not brief:
        raise HTTPException(status_code=404, detail=f"Brief {brief_id} not found")

    superseded = is_superseded(session, brief_id)

    result = BriefOut(
        id=brief.id,
        case_id=brief.case_id,
        frozen_at=brief.frozen_at,
        state=brief.state,
        superseded=superseded,
        content=brief.content,
    )
    return result
