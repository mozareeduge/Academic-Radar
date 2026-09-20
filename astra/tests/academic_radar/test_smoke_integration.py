"""Integration tests for P22d smoke scenario: funding, watch, invalidation, brief."""

import os
import subprocess
import sys
import tempfile
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from academic_radar.domain.funding import compute_gap, FundingInputs
from academic_radar.domain.invalidation import invalidate, add_dependency
from academic_radar.domain.briefs import freeze_brief, BriefBlocked
from academic_radar.watch.checks import run_watch_check
from academic_radar.evidence.snapshots import record_snapshot
from academic_radar.evidence.artifacts import create_artifact
from db.radar_models_cases import EvaluationCase
from db.radar_models_claims import Claim, FundingAssessment, ClaimEvidence, GateAssessment
from db.radar_models_evidence import SourceSnapshot, EvidenceArtifact, ResearchRun, ResearchCoverage
from db.radar_models_watch import WatchTarget
from academic_radar.domain.enums import (
    ApplicationRoute, ResearchState, UserDisposition, ApplicationStage,
    ClaimStatus, GateResult
)


def make_temp_db():
    """Create a temporary SQLite database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    normalized_path = path.replace("\\", "/")
    return f"sqlite:///{normalized_path}", path


@pytest.fixture
def db_session():
    """Fixture providing a database session with migrations applied."""
    db_url, path = make_temp_db()
    try:
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url
        astra_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=env,
            cwd=astra_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Alembic upgrade failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
        engine = create_engine(db_url)
        with Session(engine) as session:
            yield session
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture
def ma_case(db_session: Session) -> EvaluationCase:
    """Create MA case for testing."""
    from db.radar_models_targets import MozareRoute, TargetEntity

    # Create route
    route = MozareRoute(
        id="test-route",
        name="Test Route",
        state="ACTIVE",
    )
    db_session.add(route)

    # Create target entity
    target = TargetEntity(
        id="test-target",
        kind="Person",
        display_name="Test Target",
        canonical_url="http://example.com/test-target",
        source_authority="DISCOVERY_AGGREGATOR",
    )
    db_session.add(target)
    db_session.flush()

    case = EvaluationCase(
        route_id="test-route",
        target_id="test-target",
        application_route=ApplicationRoute.MA_PROGRAMME,
        research_state=ResearchState.DISCOVERED,
        user_disposition=UserDisposition.UNDECIDED,
        application_stage=ApplicationStage.NOT_STARTED,
    )
    db_session.add(case)
    db_session.flush()
    return case


@pytest.fixture
def supervisor_case(db_session: Session) -> EvaluationCase:
    """Create supervisor case for testing."""
    from db.radar_models_targets import MozareRoute, TargetEntity

    # Create route
    route = MozareRoute(
        id="test-route-sup",
        name="Test Route Sup",
        state="ACTIVE",
    )
    db_session.add(route)

    # Create target entity
    target = TargetEntity(
        id="test-target-sup",
        kind="Person",
        display_name="Test Target Sup",
        canonical_url="http://example.com/test-target-sup",
        source_authority="DISCOVERY_AGGREGATOR",
    )
    db_session.add(target)
    db_session.flush()

    case = EvaluationCase(
        route_id="test-route-sup",
        target_id="test-target-sup",
        application_route=ApplicationRoute.SUPERVISOR_FIRST_PHD,
        research_state=ResearchState.DISCOVERED,
        user_disposition=UserDisposition.UNDECIDED,
        application_stage=ApplicationStage.NOT_STARTED,
    )
    db_session.add(case)
    db_session.flush()
    return case


def test_funding_decimal_gap_computation(db_session: Session, ma_case: EvaluationCase) -> None:
    """Test that funding assessments use Decimal for gap computation."""
    # Create first funding assessment with known living cost
    inputs1 = FundingInputs(
        currency="GBP",
        annual_award=Decimal("15000"),
        fee_waiver=Decimal("0"),
        reliable_external=Decimal("0"),
        tuition=Decimal("3000"),
        mandatory_fees=Decimal("500"),
        living_costs=Decimal("15000"),
        insurance_visa_relocation=Decimal("1000"),
        duration_months=12,
    )
    result1 = compute_gap(inputs1)

    assert result1.complete is True
    assert result1.annual_gap_or_surplus == Decimal("15000") - Decimal("19500")
    assert result1.annual_gap_or_surplus == Decimal("-4500")

    # Create second funding assessment with UNKNOWN living cost (NULL)
    inputs2 = FundingInputs(
        currency="GBP",
        annual_award=Decimal("15000"),
        fee_waiver=Decimal("0"),
        reliable_external=Decimal("0"),
        tuition=Decimal("3000"),
        mandatory_fees=Decimal("500"),
        living_costs=None,  # Unknown
        insurance_visa_relocation=Decimal("1000"),
        duration_months=12,
    )
    result2 = compute_gap(inputs2)

    assert result2.complete is False
    assert result2.annual_gap_or_surplus is None  # Can't compute without living_costs
    assert "living_costs" in result2.unknown_items


def test_targeted_invalidation_on_evidence_change(
    db_session: Session, ma_case: EvaluationCase, supervisor_case: EvaluationCase
) -> None:
    """Test that changing funding evidence invalidates only MA case, not supervisor case."""
    # Create funding assessment with evidence
    snapshot = record_snapshot(
        db_session, "https://funding.example.org/ma-route", "old funding data", True
    )
    now = datetime.now(timezone.utc)
    artifact = create_artifact(
        db_session, snapshot, "https://funding.example.org/ma-route", "text/plain",
        "old funding", now.isoformat() if isinstance(now, datetime) else now
    )

    funding = FundingAssessment(
        case_id=ma_case.id,
        funding_route_id="funding-1",
        currency="GBP",
        award_amount=Decimal("15000"),
        state="ELIGIBLE",
    )
    db_session.add(funding)
    db_session.flush()

    # Link evidence directly to case (funding assessment is just a detail of the case)
    add_dependency(db_session, "SourceSnapshot", snapshot.id, "EvaluationCase", ma_case.id)

    # Link supervisor case to different evidence (to verify it stays untouched)
    sup_snapshot = record_snapshot(
        db_session, "https://supervisor.example.org", "supervisor data", True
    )
    now = datetime.now(timezone.utc)
    sup_artifact = create_artifact(
        db_session, sup_snapshot, "https://supervisor.example.org", "text/plain",
        "supervisor", now.isoformat() if isinstance(now, datetime) else now
    )
    sup_claim = Claim(
        case_id=supervisor_case.id,
        statement="Supervisor precedent",
        claim_type="EXTERNAL_FACT",
        status=ClaimStatus.SUPPORTED,
    )
    db_session.add(sup_claim)
    db_session.flush()

    ce = ClaimEvidence(claim_id=sup_claim.id, evidence_artifact_id=sup_artifact.id)
    db_session.add(ce)
    db_session.flush()

    add_dependency(db_session, "SourceSnapshot", sup_snapshot.id, "Claim", sup_claim.id)

    # Set both to EVIDENCE_READY
    ma_case.research_state = ResearchState.EVIDENCE_READY
    supervisor_case.research_state = ResearchState.EVIDENCE_READY
    db_session.flush()

    # Invalidate the MA funding snapshot
    report = invalidate(db_session, snapshot.id)

    db_session.refresh(ma_case)
    db_session.refresh(supervisor_case)

    # MA case should be STALE (via dependency chain: snapshot -> case)
    assert ma_case.research_state == ResearchState.STALE
    assert len(report.stale_cases) >= 1

    # Supervisor case must stay EVIDENCE_READY (no user_disposition changed)
    assert supervisor_case.research_state == ResearchState.EVIDENCE_READY
    assert supervisor_case.user_disposition == UserDisposition.UNDECIDED


def test_watch_change_with_material_change_event(db_session: Session) -> None:
    """Test that watch triggers a CHANGED snapshot and material change event."""
    # Create initial snapshot
    initial_snapshot = record_snapshot(
        db_session, "https://example.org/funding", "initial content\nline 2", True
    )
    db_session.flush()

    # Create watch target for this URL
    watch = WatchTarget(
        target_id="test-entity",
        url="https://example.org/funding",
        cadence="daily",
    )
    db_session.add(watch)
    db_session.flush()

    # Simulate a fetch that returns changed content
    def mock_fetch(url: str):
        return ("changed content\nline 2\nline 3", True)

    # Run watch check
    result = run_watch_check(
        db_session, {"id": watch.id, "url": watch.url}, mock_fetch,
        prior_text="initial content\nline 2"
    )

    assert result["snapshot_state"] == "CHANGED"
    assert result["change_event_id"] is not None  # Material change (>1 line different)
    assert result["summary"] is not None

    # Verify snapshot was recorded
    snapshots = db_session.query(SourceSnapshot).filter_by(source_url=watch.url).all()
    assert len(snapshots) >= 2  # initial + changed
    assert any(s.state == "CHANGED" for s in snapshots)


def test_brief_freeze_with_dependencies(
    db_session: Session, ma_case: EvaluationCase
) -> None:
    """Test that freeze_brief records dependencies."""
    # Set up MA case with research state
    ma_case.research_state = ResearchState.EVIDENCE_READY
    db_session.flush()

    # Create evidence and claim
    snapshot = record_snapshot(
        db_session, "https://ma-evidence.org", "MA data", True
    )
    now = datetime.now(timezone.utc)
    artifact = create_artifact(
        db_session, snapshot, "https://ma-evidence.org", "text/plain",
        "MA evidence", now.isoformat() if isinstance(now, datetime) else now
    )
    db_session.flush()

    claim = Claim(
        case_id=ma_case.id,
        statement="MA eligibility fact",
        claim_type="EXTERNAL_FACT",
        status=ClaimStatus.SUPPORTED,
    )
    db_session.add(claim)
    db_session.flush()

    ce = ClaimEvidence(claim_id=claim.id, evidence_artifact_id=artifact.id)
    db_session.add(ce)
    db_session.flush()

    # Create a hard gate with PASS (not UNKNOWN)
    gate = GateAssessment(
        case_id=ma_case.id,
        requirement="Formal eligibility gate",
        source_authority="OFFICIAL_REGULATION",
        result=GateResult.PASS,
        evidence_ids=["evidence-1"],
    )
    db_session.add(gate)
    db_session.flush()

    # Freeze brief
    brief_id = freeze_brief(db_session, ma_case.id)
    assert brief_id is not None

    # Verify dependencies were recorded
    from db.radar_models_watch import BriefDependency
    deps = db_session.query(BriefDependency).filter_by(brief_id=brief_id).all()
    assert len(deps) >= 1


def test_brief_blocked_by_unknown_hard_gate(db_session: Session, ma_case: EvaluationCase) -> None:
    """Test that freeze_brief raises BriefBlocked when hard gate is UNKNOWN."""
    ma_case.research_state = ResearchState.EVIDENCE_READY
    db_session.flush()

    # Create a hard gate with UNKNOWN result
    gate = GateAssessment(
        case_id=ma_case.id,
        requirement="Unknown gate",
        source_authority="OFFICIAL_REGULATION",
        result=GateResult.UNKNOWN,
    )
    db_session.add(gate)
    db_session.flush()

    # Attempt to freeze brief
    with pytest.raises(BriefBlocked) as exc_info:
        freeze_brief(db_session, ma_case.id)

    assert "Hard gate unknown" in str(exc_info.value)
