"""Dependency-targeted invalidation of claims, assessments, and suggestions.

DEC-042: Dependency-based invalidation
Changed evidence invalidates only explicitly dependent claims/assessments/suggestions/
briefs whenever the dependency graph is intact.

ORACLE-020: Evidence refresh is targeted
Evidence changes stale/recompute only dependent claims/assessments/suggestions/briefs
in normal operation; unrelated reviewed state survives.

Implementation:
  - add_dependency(session, upstream_kind, upstream_id, downstream_kind, downstream_id)
    creates an edge in radar_evidence_dependencies.

  - invalidate(session, snapshot_id) -> InvalidationReport
    walks the dependency graph DOWNSTREAM only from the changed snapshot,
    marks affected claims STALE, marks affected research_state EVIDENCE_READY -> STALE,
    never touches user_disposition, user notes, or unrelated cases.
    If a dependency edge is missing it returns unresolved_dependencies in the report.
"""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from db.radar_models_evidence import EvidenceDependency
from db.radar_models_claims import Claim, GateAssessment, FundingAssessment
from db.radar_models_cases import EvaluationCase
from academic_radar.domain.enums import ClaimStatus, GateResult, ResearchState, can_transition


@dataclass
class InvalidationReport:
    """Result of an invalidation operation."""

    stale_claims: list[str] = field(default_factory=list)
    stale_assessments: list[str] = field(default_factory=list)
    stale_suggestions: list[str] = field(default_factory=list)
    stale_briefs: list[str] = field(default_factory=list)
    stale_cases: list[str] = field(default_factory=list)
    unresolved_dependencies: list[dict] = field(default_factory=list)


def add_dependency(
    session: Session,
    upstream_kind: str,
    upstream_id: str,
    downstream_kind: str,
    downstream_id: str,
) -> None:
    """Add an explicit edge in the dependency graph.

    Args:
        session: Database session.
        upstream_kind: Type of upstream object (e.g., 'SourceSnapshot', 'Claim').
        upstream_id: ID of upstream object.
        downstream_kind: Type of downstream object (e.g., 'Claim', 'GateAssessment').
        downstream_id: ID of downstream object.
    """
    dep = EvidenceDependency(
        upstream_kind=upstream_kind,
        upstream_id=upstream_id,
        downstream_kind=downstream_kind,
        downstream_id=downstream_id,
    )
    session.add(dep)
    session.flush()


def invalidate(session: Session, snapshot_id: str) -> InvalidationReport:
    """Invalidate all objects dependent on a snapshot, transitively downstream only.

    Args:
        session: Database session.
        snapshot_id: ID of the snapshot that changed.

    Returns:
        InvalidationReport with lists of stale objects and unresolved edges.
    """
    report = InvalidationReport()
    visited = set()
    to_visit = [(snapshot_id, "SourceSnapshot")]

    while to_visit:
        current_id, current_kind = to_visit.pop(0)
        state_key = (current_kind, current_id)

        if state_key in visited:
            continue
        visited.add(state_key)

        # Find all edges where this is upstream
        edges = session.query(EvidenceDependency).filter(
            and_(
                EvidenceDependency.upstream_kind == current_kind,
                EvidenceDependency.upstream_id == current_id,
            )
        ).all()

        for edge in edges:
            downstream_kind = edge.downstream_kind
            downstream_id = edge.downstream_id

            # Mark the downstream object stale
            if downstream_kind == "Claim":
                claim = session.query(Claim).filter_by(id=downstream_id).first()
                if claim:
                    claim.status = ClaimStatus.STALE
                    report.stale_claims.append(downstream_id)
                    # Queue downstream of this claim
                    to_visit.append((downstream_id, downstream_kind))

            elif downstream_kind == "GateAssessment":
                gate = session.query(GateAssessment).filter_by(id=downstream_id).first()
                if gate:
                    gate.result = GateResult.STALE
                    report.stale_assessments.append(downstream_id)
                    # Queue downstream of this gate
                    to_visit.append((downstream_id, downstream_kind))

            elif downstream_kind == "FundingAssessment":
                funding = session.query(FundingAssessment).filter_by(
                    id=downstream_id
                ).first()
                if funding:
                    funding.state = "STALE"
                    report.stale_assessments.append(downstream_id)
                    # Queue downstream of this funding
                    to_visit.append((downstream_id, downstream_kind))

            elif downstream_kind == "EvaluationCase":
                case = session.query(EvaluationCase).filter_by(id=downstream_id).first()
                if case:
                    if can_transition(
                        ResearchState(case.research_state), ResearchState.STALE
                    ):
                        case.research_state = ResearchState.STALE
                        report.stale_cases.append(downstream_id)
                    # Queue downstream (if any edges from this case)
                    to_visit.append((downstream_id, downstream_kind))

            # If downstream_kind is not recognized, record as unresolved
            if downstream_kind not in [
                "Claim",
                "GateAssessment",
                "FundingAssessment",
                "EvaluationCase",
            ]:
                report.unresolved_dependencies.append(
                    {
                        "upstream_kind": current_kind,
                        "upstream_id": current_id,
                        "downstream_kind": downstream_kind,
                        "downstream_id": downstream_id,
                    }
                )

    session.flush()
    return report
