"""Tests for LangGraph deep-research workflow."""

import json
import pytest
from academic_radar.research.graph import build_graph
from academic_radar.research.provider import MockProvider
from academic_radar.domain.protocols import Protocol
from academic_radar.domain.enums import CoverageStatus, ApplicationRoute


@pytest.fixture
def supervisor_first_protocol():
    """SUPERVISOR_FIRST_PHD protocol with mandatory classes."""
    return Protocol(
        application_route=ApplicationRoute.SUPERVISOR_FIRST_PHD.value,
        version="1.0",
        mandatory=(
            "RESOLVE_IDENTITY",
            "CURRENT_CONTEXT",
            "RESEARCH_SPINE",
            "SUPERVISED_PROJECTS",
        ),
        optional=(
            "CONCEPT_METHOD_GENEALOGY",
            "FUNDING_CONTEXT",
            "ROUTE_TRANSLATION",
        ),
        allow_zero_result=False,
        allowed_unknowns=(),
        blocking_unknowns=(),
        freshness_days={},
    )


@pytest.fixture
def evidence_lookup():
    """Sample evidence lookup."""
    return {
        "EVD001": {"type": "OFFICIAL_PROGRAMME", "title": "ORCID Profile"},
        "EVD002": {"type": "PRIMARY_RESEARCH_OUTPUT", "title": "Recent Publication"},
        "EVD003": {"type": "OFFICIAL_DEPARTMENT_OR_PERSON", "title": "Institutional Page"},
        "EVD004": {"type": "AUTHORITATIVE_REGISTRY", "title": "Thesis Record"},
    }


def test_happy_path_all_mandatory_found(supervisor_first_protocol, evidence_lookup):
    """Test: happy path where all mandatory classes get SEARCHED_FOUND coverage."""
    script = {
        "01_resolve_identity": json.dumps({
            "schema_version": "1",
            "node": "01_resolve_identity",
            "claims": [
                {
                    "statement": "Identity resolved via ORCID",
                    "claim_type": "EXTERNAL_FACT",
                    "evidence_ids": ["EVD001"],
                    "protocol_class": "RESOLVE_IDENTITY",
                }
            ],
            "coverage": {"RESOLVE_IDENTITY": "SEARCHED_FOUND"},
        }),
        "02_current_context_formal_route": json.dumps({
            "schema_version": "1",
            "node": "02_current_context_formal_route",
            "claims": [],
            "coverage": {"CURRENT_CONTEXT": "SEARCHED_FOUND"},
        }),
        "03_recent_research_spine": json.dumps({
            "schema_version": "1",
            "node": "03_recent_research_spine",
            "claims": [
                {
                    "statement": "Published 5 papers in last 3 years",
                    "claim_type": "EXTERNAL_FACT",
                    "evidence_ids": ["EVD002"],
                    "protocol_class": "RESEARCH_SPINE",
                }
            ],
            "coverage": {"RESEARCH_SPINE": "SEARCHED_FOUND"},
        }),
        "04_supervised_projects": json.dumps({
            "schema_version": "1",
            "node": "04_supervised_projects",
            "claims": [
                {
                    "statement": "Supervised 3 PhD students",
                    "claim_type": "EXTERNAL_FACT",
                    "evidence_ids": ["EVD004"],
                    "protocol_class": "SUPERVISED_PROJECTS",
                }
            ],
            "coverage": {"SUPERVISED_PROJECTS": "SEARCHED_FOUND"},
        }),
        "05_concept_method_corpus_genealogy": json.dumps({
            "schema_version": "1",
            "node": "05_concept_method_corpus_genealogy",
            "claims": [],
            "coverage": {},
        }),
        "06_project_funding_context": json.dumps({
            "schema_version": "1",
            "node": "06_project_funding_context",
            "claims": [],
            "coverage": {},
        }),
        "07_route_translation": json.dumps({
            "schema_version": "1",
            "node": "07_route_translation",
            "claims": [],
            "coverage": {},
        }),
        "08_contradictions_unknowns": json.dumps({
            "schema_version": "1",
            "node": "08_contradictions_unknowns",
            "claims": [],
            "coverage": {},
        }),
        "09_structured_synthesis": json.dumps({
            "schema_version": "1",
            "node": "09_structured_synthesis",
            "claims": [],
            "coverage": {},
        }),
    }

    provider = MockProvider(script)
    graph = build_graph(provider, supervisor_first_protocol, evidence_lookup)

    initial_state = {
        "case_state": {},
        "sources": [],
    }

    result = graph.invoke(initial_state)

    # Check that readiness is computed and True
    assert result["readiness"]["ready"] is True
    assert result["readiness"]["missing"] == []
    assert result["readiness"]["blocked"] == []

    # Check that claims accumulated
    assert len(result["claims"]) == 3

    # Check that coverage has all mandatory classes
    assert result["coverage"]["RESOLVE_IDENTITY"] == CoverageStatus.SEARCHED_FOUND
    assert result["coverage"]["CURRENT_CONTEXT"] == CoverageStatus.SEARCHED_FOUND
    assert result["coverage"]["RESEARCH_SPINE"] == CoverageStatus.SEARCHED_FOUND
    assert result["coverage"]["SUPERVISED_PROJECTS"] == CoverageStatus.SEARCHED_FOUND


def test_node_04_malformed_json(supervisor_first_protocol, evidence_lookup):
    """Test: node 04 returns malformed JSON => SUPERVISED_PROJECTS stays NOT_SEARCHED => ready False."""
    script = {
        "01_resolve_identity": json.dumps({
            "schema_version": "1",
            "node": "01_resolve_identity",
            "claims": [
                {
                    "statement": "Identity resolved",
                    "claim_type": "EXTERNAL_FACT",
                    "evidence_ids": ["EVD001"],
                    "protocol_class": "RESOLVE_IDENTITY",
                }
            ],
            "coverage": {"RESOLVE_IDENTITY": "SEARCHED_FOUND"},
        }),
        "02_current_context_formal_route": json.dumps({
            "schema_version": "1",
            "node": "02_current_context_formal_route",
            "claims": [],
            "coverage": {"CURRENT_CONTEXT": "SEARCHED_FOUND"},
        }),
        "03_recent_research_spine": json.dumps({
            "schema_version": "1",
            "node": "03_recent_research_spine",
            "claims": [],
            "coverage": {"RESEARCH_SPINE": "SEARCHED_FOUND"},
        }),
        "04_supervised_projects": "{ invalid json",  # Malformed
        "05_concept_method_corpus_genealogy": json.dumps({
            "schema_version": "1",
            "node": "05_concept_method_corpus_genealogy",
            "claims": [],
            "coverage": {},
        }),
        "06_project_funding_context": json.dumps({
            "schema_version": "1",
            "node": "06_project_funding_context",
            "claims": [],
            "coverage": {},
        }),
        "07_route_translation": json.dumps({
            "schema_version": "1",
            "node": "07_route_translation",
            "claims": [],
            "coverage": {},
        }),
        "08_contradictions_unknowns": json.dumps({
            "schema_version": "1",
            "node": "08_contradictions_unknowns",
            "claims": [],
            "coverage": {},
        }),
        "09_structured_synthesis": json.dumps({
            "schema_version": "1",
            "node": "09_structured_synthesis",
            "claims": [],
            "coverage": {},
        }),
    }

    provider = MockProvider(script)
    graph = build_graph(provider, supervisor_first_protocol, evidence_lookup)

    initial_state = {
        "case_state": {},
        "sources": [],
    }

    result = graph.invoke(initial_state)

    # SUPERVISED_PROJECTS should stay NOT_SEARCHED
    assert result["coverage"].get("SUPERVISED_PROJECTS", CoverageStatus.NOT_SEARCHED) == CoverageStatus.NOT_SEARCHED

    # Prior claims untouched (only 2 from nodes 1-3)
    assert len(result["claims"]) == 1

    # Readiness should be False
    assert result["readiness"]["ready"] is False
    assert "SUPERVISED_PROJECTS" in result["readiness"]["missing"]

    # Diagnostic recorded
    assert len(result["diagnostics"]) == 1
    assert "04_supervised_projects" in result["diagnostics"][0]["node"]


def test_node_04_explicit_searched_none_found(supervisor_first_protocol, evidence_lookup):
    """Test: node 04 returns SEARCHED_NONE_FOUND with valid structure => class satisfied => ready True."""
    script = {
        "01_resolve_identity": json.dumps({
            "schema_version": "1",
            "node": "01_resolve_identity",
            "claims": [
                {
                    "statement": "Identity resolved",
                    "claim_type": "EXTERNAL_FACT",
                    "evidence_ids": ["EVD001"],
                    "protocol_class": "RESOLVE_IDENTITY",
                }
            ],
            "coverage": {"RESOLVE_IDENTITY": "SEARCHED_FOUND"},
        }),
        "02_current_context_formal_route": json.dumps({
            "schema_version": "1",
            "node": "02_current_context_formal_route",
            "claims": [],
            "coverage": {"CURRENT_CONTEXT": "SEARCHED_FOUND"},
        }),
        "03_recent_research_spine": json.dumps({
            "schema_version": "1",
            "node": "03_recent_research_spine",
            "claims": [],
            "coverage": {"RESEARCH_SPINE": "SEARCHED_FOUND"},
        }),
        "04_supervised_projects": json.dumps({
            "schema_version": "1",
            "node": "04_supervised_projects",
            "claims": [],
            "coverage": {"SUPERVISED_PROJECTS": "SEARCHED_NONE_FOUND"},
        }),
        "05_concept_method_corpus_genealogy": json.dumps({
            "schema_version": "1",
            "node": "05_concept_method_corpus_genealogy",
            "claims": [],
            "coverage": {},
        }),
        "06_project_funding_context": json.dumps({
            "schema_version": "1",
            "node": "06_project_funding_context",
            "claims": [],
            "coverage": {},
        }),
        "07_route_translation": json.dumps({
            "schema_version": "1",
            "node": "07_route_translation",
            "claims": [],
            "coverage": {},
        }),
        "08_contradictions_unknowns": json.dumps({
            "schema_version": "1",
            "node": "08_contradictions_unknowns",
            "claims": [],
            "coverage": {},
        }),
        "09_structured_synthesis": json.dumps({
            "schema_version": "1",
            "node": "09_structured_synthesis",
            "claims": [],
            "coverage": {},
        }),
    }

    # Modify protocol to allow_zero_result=True for SUPERVISED_PROJECTS
    protocol = Protocol(
        application_route=ApplicationRoute.SUPERVISOR_FIRST_PHD.value,
        version="1.0",
        mandatory=(
            "RESOLVE_IDENTITY",
            "CURRENT_CONTEXT",
            "RESEARCH_SPINE",
            "SUPERVISED_PROJECTS",
        ),
        optional=(),
        allow_zero_result=True,  # Allow zero results
        allowed_unknowns=(),
        blocking_unknowns=(),
        freshness_days={},
    )

    provider = MockProvider(script)
    graph = build_graph(provider, protocol, evidence_lookup)

    initial_state = {
        "case_state": {},
        "sources": [],
    }

    result = graph.invoke(initial_state)

    # SUPERVISED_PROJECTS satisfied with SEARCHED_NONE_FOUND
    assert result["coverage"]["SUPERVISED_PROJECTS"] == CoverageStatus.SEARCHED_NONE_FOUND

    # Readiness should be True
    assert result["readiness"]["ready"] is True
    assert result["readiness"]["missing"] == []
