"""api.routes.radar_evidence — Evidence inspector, research runs, coverage API endpoints.

Implements:
- GET /claims/{id}/evidence: evidence artifacts with source_url, authority, retrieved_at, excerpt, independent_support_count, contradiction state
- GET /cases/{id}/coverage: per evidence class CoverageStatus + evidence ids + protocol version
- POST /cases/{id}/research: enqueues research job with generated run_key; returns run id
- GET /runs/{id}: status, failure reason, run identity without secrets
"""

from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from db.models import User
from db.radar_models_cases import EvaluationCase
from db.radar_models_evidence import EvidenceArtifact, ResearchRun, ResearchCoverage
from db.radar_models_claims import Claim, ClaimEvidence
from academic_radar.security.redact import redact

router = APIRouter(prefix="/api/radar", tags=["radar"])


class EvidenceArtifactOut(BaseModel):
    """Single evidence artifact."""
    id: str
    source_url: str
    authority: str
    retrieved_at: datetime
    excerpt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceOut(BaseModel):
    """Evidence inspector response."""
    artifacts: list[EvidenceArtifactOut]
    independent_support_count: int
    contradiction_state: str


class CoverageItemOut(BaseModel):
    """Coverage status for one evidence class."""
    evidence_class: str
    status: str
    evidence_ids: list[str]


class CoverageOut(BaseModel):
    """Coverage response with protocol version."""
    coverage: list[CoverageItemOut]
    protocol_version: str


class ResearchPostIn(BaseModel):
    """Request to start research."""
    run_key: Optional[str] = None


class ResearchPostOut(BaseModel):
    """Response from POST /research."""
    run_id: str


class RunIdentityOut(BaseModel):
    """Run identity without secrets."""
    model_id: Optional[str] = None
    provider_id: Optional[str] = None
    prompt_hash: Optional[str] = None
    schema_version: Optional[str] = None
    protocol_version: Optional[str] = None
    run_id: Optional[str] = None


class RunOut(BaseModel):
    """Run status and identity."""
    status: str
    failure_reason: Optional[str] = None
    run_identity: Optional[RunIdentityOut] = None


@router.get("/claims/{claim_id}/evidence", response_model=EvidenceOut)
def get_evidence(
    claim_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> EvidenceOut:
    """Get evidence artifacts linked to a claim.

    Returns source_url, authority, retrieved_at, excerpt for each artifact,
    plus independent_support_count and contradiction state.
    """
    claim = session.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")

    # Get evidence links for this claim
    links = session.query(ClaimEvidence).filter(
        ClaimEvidence.claim_id == claim_id
    ).all()

    artifacts_out = []
    seen_origins = set()
    independent_count = 0

    for link in links:
        artifact = session.query(EvidenceArtifact).filter(
            EvidenceArtifact.id == link.evidence_artifact_id
        ).first()
        if not artifact:
            continue

        artifacts_out.append(EvidenceArtifactOut(
            id=artifact.id,
            source_url=artifact.source_url,
            authority=artifact.source_authority,
            retrieved_at=artifact.retrieved_at,
            excerpt=artifact.excerpt
        ))

        # Count independent support: each unique canonical_origin counts once
        origin = artifact.canonical_origin or artifact.source_url
        if origin not in seen_origins:
            seen_origins.add(origin)
            independent_count += 1

    return EvidenceOut(
        artifacts=artifacts_out,
        independent_support_count=independent_count,
        contradiction_state=claim.status
    )


@router.get("/cases/{case_id}/coverage", response_model=CoverageOut)
def get_coverage(
    case_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CoverageOut:
    """Get research coverage for a case.

    Returns per-evidence-class coverage status, evidence ids, and protocol version.
    """
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Get the most recent research run for this case
    run = session.query(ResearchRun).filter(
        ResearchRun.case_id == case_id
    ).order_by(ResearchRun.created_at.desc()).first()

    if not run:
        raise HTTPException(status_code=404, detail=f"No research run found for case {case_id}")

    # Get all coverage records for this run
    coverage_records = session.query(ResearchCoverage).filter(
        ResearchCoverage.run_id == run.id
    ).all()

    coverage_items = [
        CoverageItemOut(
            evidence_class=c.evidence_class,
            status=c.status,
            evidence_ids=c.evidence_ids or []
        )
        for c in coverage_records
    ]

    return CoverageOut(
        coverage=coverage_items,
        protocol_version=run.protocol_version
    )


@router.post("/cases/{case_id}/research", response_model=ResearchPostOut, status_code=202)
def post_research(
    case_id: str,
    body: ResearchPostIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ResearchPostOut:
    """Start a research run for a case.

    If run_key is provided, idempotently returns the existing run for that key.
    Otherwise generates a new run_key.
    """
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # If run_key provided, check for existing run with that key
    run_key = body.run_key
    if run_key:
        # Search all runs for this case and check run_identity
        runs = session.query(ResearchRun).filter(
            ResearchRun.case_id == case_id
        ).all()
        for r in runs:
            if r.run_identity and r.run_identity.get("run_id") == run_key:
                return ResearchPostOut(run_id=r.id)

    # Create new research run
    run = ResearchRun(
        case_id=case_id,
        protocol_version="1.0",
        status="QUEUED"
    )
    session.add(run)
    session.flush()

    # Set run_identity with run_key (or use run.id as the key)
    key_for_identity = run_key or run.id
    run.run_identity = {
        "run_id": key_for_identity
    }
    session.commit()

    return ResearchPostOut(run_id=run.id)


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(
    run_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> RunOut:
    """Get research run status and identity.

    Run identity contains no secrets.
    """
    run = session.query(ResearchRun).filter(ResearchRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    run_identity_out = None
    if run.run_identity:
        # Verify no secrets in run_identity before returning
        identity_str = str(run.run_identity)
        redacted = redact(identity_str)
        if redacted != identity_str:
            raise HTTPException(
                status_code=500,
                detail="Run identity contains secrets (internal error)"
            )

        run_identity_out = RunIdentityOut(
            model_id=run.run_identity.get("model_id"),
            provider_id=run.run_identity.get("provider_id"),
            prompt_hash=run.run_identity.get("prompt_hash"),
            schema_version=run.run_identity.get("schema_version"),
            protocol_version=run.run_identity.get("protocol_version"),
            run_id=run.run_identity.get("run_id")
        )

    return RunOut(
        status=run.status,
        failure_reason=None,
        run_identity=run_identity_out
    )
