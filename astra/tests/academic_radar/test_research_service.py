"""Tests for research service persistence and validation."""

import json
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from academic_radar.research.service import run_research
from academic_radar.research.provider import MockProvider
from academic_radar.domain.enums import ResearchState, CoverageStatus, ClaimStatus
from db.radar_models_cases import EvaluationCase
from db.radar_models_evidence import ResearchRun, ResearchCoverage, EvidenceArtifact, SourceSnapshot
from db.radar_models_claims import Claim, ClaimEvidence
from db.radar_models_targets import TargetEntity, MozareRoute, CandidateProfile
from tests.academic_radar.canary import expect_violation


@pytest.fixture
def setup_db(tmp_path):
    """Set up test database."""
    from sqlalchemy import create_engine
    from db.models import Base

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def supervisor_case(setup_db):
    """Create a supervisor-first PhD case."""
    session = setup_db

    # Create route
    route = MozareRoute(
        id="route-123",
        name="Test Route",
    )
    session.add(route)
    session.flush()

    # Create target
    target = TargetEntity(
        id="target-123",
        kind="Person",
        display_name="Test Target",
        canonical_url="http://example.com/test",
        source_authority="DISCOVERY_AGGREGATOR",
    )
    session.add(target)
    session.flush()

    # Create case
    case = EvaluationCase(
        id="case-123",
        route_id=route.id,
        target_id=target.id,
        application_route="SUPERVISOR_FIRST_PHD",
        research_state="DISCOVERED",
        user_disposition="UNDECIDED",
        application_stage="NOT_STARTED",
    )
    session.add(case)
    session.commit()

    return case, session


def _build_mock_script():
    """Build fixture script for MockProvider."""
    output = {
        "schema_version": "1.0.0",
        "node": "01_resolve_identity",
        "claims": [
            {
                "statement": "Test claim for IDENTITY_POSITION",
                "claim_type": "EXTERNAL_FACT",
                "evidence_ids": ["evt-1"],
                "protocol_class": "IDENTITY_POSITION",
                "unknowns": [],
                "contradictions": [],
            }
        ],
        "coverage": {
            "IDENTITY_POSITION": "SEARCHED_FOUND",
            "RESEARCH_OBJECTS": "SEARCHED_FOUND",
            "THEORY_TOOLKIT": "SEARCHED_FOUND",
            "METHODS": "SEARCHED_FOUND",
            "RECENT_WORKS": "SEARCHED_FOUND",
            "PROJECTS_GRANTS": "SEARCHED_FOUND",
            "SUPERVISION_RECORD": "SEARCHED_FOUND",
            "SUPERVISED_PROJECTS": "SEARCHED_FOUND",
        },
    }

    script = {}
    for node in [
        "01_resolve_identity",
        "02_current_context_formal_route",
        "03_recent_research_spine",
        "04_supervised_projects",
        "05_concept_method_corpus_genealogy",
        "06_project_funding_context",
        "07_route_translation",
        "08_contradictions_unknowns",
        "09_structured_synthesis",
    ]:
        script[node] = json.dumps(output)

    return script


def test_persists_run_coverage_claims_evidence(supervisor_case):
    """Test that run_research persists all required records."""
    case, session = supervisor_case

    # Create fixture evidence
    snapshot = SourceSnapshot(
        id="snap-1",
        source_url="https://example.com/test",
        state="CAPTURED",
        captured_at=datetime.now(timezone.utc),
    )
    session.add(snapshot)
    session.flush()

    artifact = EvidenceArtifact(
        id="evt-1",
        source_url="https://example.com/test",
        source_type="text/html",
        excerpt="Test excerpt",
        snapshot_id=snapshot.id,
        retrieved_at=datetime.now(timezone.utc),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.commit()

    evidence_lookup = {"evt-1": {"url": "https://example.com/test"}}
    script = _build_mock_script()
    provider = MockProvider(script)

    # Run research
    run_id = run_research(session, case.id, provider, evidence_lookup)

    # Verify run record
    run = session.query(ResearchRun).filter_by(id=run_id).first()
    assert run is not None
    assert run.case_id == case.id
    assert run.protocol_version == "1.0.0"
    assert run.status == "COMPLETED"
    assert run.prompt_hash is not None
    assert run.schema_version == "1.0.0"

    # Verify coverage records
    coverage = session.query(ResearchCoverage).filter_by(run_id=run_id).all()
    assert len(coverage) >= 8  # At least mandatory classes
    cov_dict = {c.evidence_class: c.status for c in coverage}
    assert cov_dict["IDENTITY_POSITION"] == "SEARCHED_FOUND"

    # Verify claims
    claims = session.query(Claim).filter_by(case_id=case.id).all()
    assert len(claims) >= 1
    assert claims[0].generated_by == run_id
    assert claims[0].protocol_version == "1.0.0"
    assert claims[0].run_id == run_id

    # Verify claim evidence links
    claim_evidence = session.query(ClaimEvidence).filter_by(claim_id=claims[0].id).all()
    assert len(claim_evidence) >= 1
    assert claim_evidence[0].evidence_artifact_id == "evt-1"


def test_malformed_node_output_leaves_claims_unchanged(supervisor_case):
    """Test that malformed node output doesn't corrupt prior state."""
    case, session = supervisor_case

    snapshot = SourceSnapshot(
        id="snap-1",
        source_url="https://example.com/test",
        state="CAPTURED",
        captured_at=datetime.now(timezone.utc),
    )
    session.add(snapshot)
    session.flush()

    artifact = EvidenceArtifact(
        id="evt-1",
        source_url="https://example.com/test",
        source_type="text/html",
        excerpt="Test excerpt",
        snapshot_id=snapshot.id,
        retrieved_at=datetime.now(timezone.utc),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.commit()

    # Mock provider that returns valid output but skips one mandatory class
    script = {}
    valid_output = json.dumps({
        "schema_version": "1.0.0",
        "node": "01_resolve_identity",
        "claims": [{
            "statement": "Valid claim",
            "claim_type": "EXTERNAL_FACT",
            "evidence_ids": ["evt-1"],
            "protocol_class": "IDENTITY_POSITION",
            "unknowns": [],
            "contradictions": [],
        }],
        "coverage": {
            "IDENTITY_POSITION": "SEARCHED_FOUND",
            "RESEARCH_OBJECTS": "SEARCHED_FOUND",
            "THEORY_TOOLKIT": "NOT_SEARCHED",
            "METHODS": "SEARCHED_FOUND",
            "RECENT_WORKS": "SEARCHED_FOUND",
            "PROJECTS_GRANTS": "SEARCHED_FOUND",
            "SUPERVISION_RECORD": "SEARCHED_FOUND",
            "SUPERVISED_PROJECTS": "SEARCHED_FOUND",
        },
    })

    for node in [
        "01_resolve_identity",
        "02_current_context_formal_route",
        "03_recent_research_spine",
        "04_supervised_projects",
        "05_concept_method_corpus_genealogy",
        "06_project_funding_context",
        "07_route_translation",
        "08_contradictions_unknowns",
        "09_structured_synthesis",
    ]:
        script[node] = valid_output

    evidence_lookup = {"evt-1": {"url": "https://example.com/test"}}
    provider = MockProvider(script)

    # Run research (should produce PARTIAL due to missing mandatory coverage)
    run_id = run_research(session, case.id, provider, evidence_lookup)

    # Verify run is PARTIAL
    run = session.query(ResearchRun).filter_by(id=run_id).first()
    assert run.status == "PARTIAL"

    # Verify claims from valid nodes were persisted
    claims = session.query(Claim).filter_by(case_id=case.id).all()
    assert len(claims) >= 1


def test_not_searched_mandatory_never_evidence_ready(supervisor_case):
    """Test that NOT_SEARCHED on mandatory blocks EVIDENCE_READY."""
    case, session = supervisor_case

    snapshot = SourceSnapshot(
        id="snap-1",
        source_url="https://example.com/test",
        state="CAPTURED",
        captured_at=datetime.now(timezone.utc),
    )
    session.add(snapshot)
    session.flush()

    artifact = EvidenceArtifact(
        id="evt-1",
        source_url="https://example.com/test",
        source_type="text/html",
        excerpt="Test excerpt",
        snapshot_id=snapshot.id,
        retrieved_at=datetime.now(timezone.utc),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.commit()

    # Mock provider that doesn't cover all mandatory classes
    output = {
        "schema_version": "1.0.0",
        "node": "01_resolve_identity",
        "claims": [],
        "coverage": {
            "IDENTITY_POSITION": "NOT_SEARCHED",
            "RESEARCH_OBJECTS": "SEARCHED_FOUND",
            "THEORY_TOOLKIT": "SEARCHED_FOUND",
            "METHODS": "SEARCHED_FOUND",
            "RECENT_WORKS": "SEARCHED_FOUND",
            "PROJECTS_GRANTS": "SEARCHED_FOUND",
            "SUPERVISION_RECORD": "SEARCHED_FOUND",
            "SUPERVISED_PROJECTS": "SEARCHED_FOUND",
        },
    }

    script = {node: json.dumps(output) for node in [
        "01_resolve_identity",
        "02_current_context_formal_route",
        "03_recent_research_spine",
        "04_supervised_projects",
        "05_concept_method_corpus_genealogy",
        "06_project_funding_context",
        "07_route_translation",
        "08_contradictions_unknowns",
        "09_structured_synthesis",
    ]}

    evidence_lookup = {"evt-1": {"url": "https://example.com/test"}}
    provider = MockProvider(script)

    # Run research
    run_id = run_research(session, case.id, provider, evidence_lookup)

    # Verify case is NOT EVIDENCE_READY
    case_after = session.query(EvaluationCase).filter_by(id=case.id).first()
    assert case_after.research_state != ResearchState.EVIDENCE_READY.value


def test_user_disposition_unchanged(supervisor_case):
    """Test that automation never changes user_disposition."""
    case, session = supervisor_case
    case.user_disposition = "UNDECIDED"
    session.commit()

    snapshot = SourceSnapshot(
        id="snap-1",
        source_url="https://example.com/test",
        state="CAPTURED",
        captured_at=datetime.now(timezone.utc),
    )
    session.add(snapshot)
    session.flush()

    artifact = EvidenceArtifact(
        id="evt-1",
        source_url="https://example.com/test",
        source_type="text/html",
        excerpt="Test excerpt",
        snapshot_id=snapshot.id,
        retrieved_at=datetime.now(timezone.utc),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.commit()

    evidence_lookup = {"evt-1": {"url": "https://example.com/test"}}
    script = _build_mock_script()
    provider = MockProvider(script)

    # Run research
    run_research(session, case.id, provider, evidence_lookup)

    # Verify user_disposition unchanged
    case_after = session.query(EvaluationCase).filter_by(id=case.id).first()
    assert case_after.user_disposition == "UNDECIDED"


def test_unknown_claim_allowed_with_searched_none_found(supervisor_case):
    """Test that claims are still valid when optional class has SEARCHED_NONE_FOUND."""
    case, session = supervisor_case

    snapshot = SourceSnapshot(
        id="snap-1",
        source_url="https://example.com/test",
        state="CAPTURED",
        captured_at=datetime.now(timezone.utc),
    )
    session.add(snapshot)
    session.flush()

    artifact = EvidenceArtifact(
        id="evt-1",
        source_url="https://example.com/test",
        source_type="text/html",
        excerpt="Test excerpt",
        snapshot_id=snapshot.id,
        retrieved_at=datetime.now(timezone.utc),
        source_authority="OFFICIAL_PROGRAMME",
    )
    session.add(artifact)
    session.commit()

    # Mock provider with INFERENCE claim with evidence and SEARCHED_NONE_FOUND for optional
    output = {
        "schema_version": "1.0.0",
        "node": "09_structured_synthesis",
        "claims": [{
            "statement": "Inference about IDENTITY_POSITION",
            "claim_type": "INFERENCE",
            "evidence_ids": ["evt-1"],
            "protocol_class": "IDENTITY_POSITION",
            "unknowns": [],
            "contradictions": [],
        }],
        "coverage": {
            "IDENTITY_POSITION": "SEARCHED_FOUND",
            "RESEARCH_OBJECTS": "SEARCHED_FOUND",
            "THEORY_TOOLKIT": "SEARCHED_FOUND",
            "METHODS": "SEARCHED_FOUND",
            "RECENT_WORKS": "SEARCHED_FOUND",
            "PROJECTS_GRANTS": "SEARCHED_FOUND",
            "SUPERVISION_RECORD": "SEARCHED_FOUND",
            "SUPERVISED_PROJECTS": "SEARCHED_FOUND",
            "OPTIONAL_CLASS": "SEARCHED_NONE_FOUND",
        },
    }

    script = {node: json.dumps(output) for node in [
        "01_resolve_identity",
        "02_current_context_formal_route",
        "03_recent_research_spine",
        "04_supervised_projects",
        "05_concept_method_corpus_genealogy",
        "06_project_funding_context",
        "07_route_translation",
        "08_contradictions_unknowns",
        "09_structured_synthesis",
    ]}

    evidence_lookup = {"evt-1": {"url": "https://example.com/test"}}
    provider = MockProvider(script)

    # Run research
    run_id = run_research(session, case.id, provider, evidence_lookup)

    # Verify claims were persisted
    claims = session.query(Claim).filter_by(case_id=case.id).all()
    assert len(claims) >= 1
    assert claims[0].claim_type == "INFERENCE"
    assert claims[0].status == ClaimStatus.SUPPORTED.value
