"""Tests for versioned protocol definitions and loader.

ORACLE-008, ORACLE-009: Protocol completeness and readiness computation.
Requires five versioned protocols in protocols.yaml and load_protocols() loader.
"""

import pytest
from academic_radar.research.protocol_loader import load_protocols


class TestProtocolLoader:
    """Test five protocol definitions and loader."""

    # ORACLE-008, ORACLE-009
    def test_load_protocols_returns_dict(self):
        """load_protocols() returns dict with correct keys."""
        protocols = load_protocols()
        assert isinstance(protocols, dict)
        expected_keys = {
            "SUPERVISOR_FIRST_PHD",
            "ADVERTISED_PHD",
            "STRUCTURED_PHD",
            "MA_PROGRAMME",
            "FUNDING_ASSESSMENT",
        }
        assert set(protocols.keys()) == expected_keys

    def test_supervisor_first_phd_protocol(self):
        """SUPERVISOR_FIRST_PHD has correct version and fields."""
        protocols = load_protocols()
        proto = protocols["SUPERVISOR_FIRST_PHD"]
        assert proto.version == "1.0.0"
        assert proto.application_route == "SUPERVISOR_FIRST_PHD"

        # Check mandatory
        expected_mandatory = {
            "IDENTITY_POSITION",
            "RESEARCH_OBJECTS",
            "THEORY_TOOLKIT",
            "METHODS",
            "RECENT_WORKS",
            "PROJECTS_GRANTS",
            "SUPERVISION_RECORD",
            "SUPERVISED_PROJECTS",
        }
        assert set(proto.mandatory) == expected_mandatory

        # Check optional
        expected_optional = {
            "CONCEPT_METHOD_GENEALOGY",
            "CO_SUPERVISION_PATTERNS",
            "FUNDING_ATTACHED_TO_PRECEDENTS",
        }
        assert set(proto.optional) == expected_optional

        assert proto.allow_zero_result is True
        assert "IDENTITY_POSITION" in proto.blocking_unknowns

    def test_advertised_phd_protocol(self):
        """ADVERTISED_PHD has correct version and fields."""
        protocols = load_protocols()
        proto = protocols["ADVERTISED_PHD"]
        assert proto.version == "1.0.0"
        assert proto.application_route == "ADVERTISED_PHD"

        # Check mandatory
        expected_mandatory = {
            "VACANCY_TERMS",
            "FORMAL_ELIGIBILITY",
            "DEADLINE",
            "SUPERVISOR_IDENTITY",
            "PROJECT_DESCRIPTION",
            "APPLICATION_PROCEDURE",
        }
        assert set(proto.mandatory) == expected_mandatory

        # Check optional
        expected_optional = {"SUPERVISOR_SPINE"}
        assert set(proto.optional) == expected_optional

        assert proto.allow_zero_result is False

    def test_structured_phd_protocol(self):
        """STRUCTURED_PHD has correct version and fields."""
        protocols = load_protocols()
        proto = protocols["STRUCTURED_PHD"]
        assert proto.version == "1.0.0"
        assert proto.application_route == "STRUCTURED_PHD"

        # Check mandatory
        expected_mandatory = {
            "PROGRAMME_STRUCTURE",
            "ADMISSION_RULES",
            "FUNDING_ROUTES",
            "DEADLINE",
            "SUPERVISOR_MATCHING_PROCEDURE",
        }
        assert set(proto.mandatory) == expected_mandatory

        # Check optional
        expected_optional = {"PAST_COHORT_EVIDENCE"}
        assert set(proto.optional) == expected_optional

    def test_ma_programme_protocol(self):
        """MA_PROGRAMME has correct version and fields."""
        protocols = load_protocols()
        proto = protocols["MA_PROGRAMME"]
        assert proto.version == "1.0.0"
        assert proto.application_route == "MA_PROGRAMME"

        # Check mandatory
        expected_mandatory = {
            "FORMAL_ELIGIBILITY",
            "CURRICULUM_FIT",
            "ENGLISH_REQUIREMENT",
            "DEADLINE",
            "EXISTING_MA_RULE",
        }
        assert set(proto.mandatory) == expected_mandatory

        # Check optional
        expected_optional = {"COMMITTEE_EVIDENCE", "NARRATIVE_INPUTS"}
        assert set(proto.optional) == expected_optional

        assert proto.allow_zero_result is False

    def test_funding_assessment_protocol(self):
        """FUNDING_ASSESSMENT has correct version and fields."""
        protocols = load_protocols()
        proto = protocols["FUNDING_ASSESSMENT"]
        assert proto.version == "1.0.0"
        assert proto.application_route == "FUNDING_ASSESSMENT"

        # Check mandatory
        expected_mandatory = {
            "SCHOLARSHIP_ELIGIBILITY",
            "NOMINATION_ROUTE",
            "AWARD_TERMS",
            "TUITION_FEES",
            "COST_INPUTS",
            "DEADLINE",
        }
        assert set(proto.mandatory) == expected_mandatory

        # Check optional
        expected_optional = {"INCOMPATIBILITY_RULES"}
        assert set(proto.optional) == expected_optional

    def test_all_protocols_have_freshness_days(self):
        """All protocols have freshness_days dict with correct defaults."""
        protocols = load_protocols()
        for proto in protocols.values():
            assert isinstance(proto.freshness_days, dict)
            # Check that DEADLINE has 30 days
            assert proto.freshness_days.get("DEADLINE") == 30
            # Check that FORMAL_ELIGIBILITY has 90 days
            if "FORMAL_ELIGIBILITY" in proto.mandatory or "FORMAL_ELIGIBILITY" in proto.optional:
                assert proto.freshness_days.get("FORMAL_ELIGIBILITY") == 90
            # Check other keys have 180
            for key in proto.mandatory + proto.optional:
                if key not in ("DEADLINE", "FORMAL_ELIGIBILITY"):
                    assert proto.freshness_days.get(key) == 180

    def test_loading_twice_yields_equal_objects(self):
        """Loading protocols twice yields equal objects."""
        proto1 = load_protocols()
        proto2 = load_protocols()

        assert set(proto1.keys()) == set(proto2.keys())
        for key in proto1.keys():
            assert proto1[key] == proto2[key]

    def test_unknown_route_key_raises_keyerror(self):
        """Accessing unknown route key raises KeyError."""
        protocols = load_protocols()
        with pytest.raises(KeyError):
            _ = protocols["UNKNOWN_ROUTE"]
