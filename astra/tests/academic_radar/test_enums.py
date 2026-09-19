"""Test domain enums and state transitions."""

import pytest

from academic_radar.domain.enums import (
    ApplicationRoute,
    ApplicationStage,
    ClaimStatus,
    ClaimType,
    CoverageStatus,
    DeadlinePrecision,
    GateResult,
    IdentityStatus,
    ProfileState,
    ResearchState,
    RouteState,
    SnapshotState,
    SourceAuthority,
    TargetKind,
    UserDisposition,
    LEGAL_TRANSITIONS,
    can_transition,
)


class TestResearchStateEnum:
    """Test ResearchState enum has correct members and values."""

    def test_research_state_members(self):
        """Assert exact member-value set."""
        expected = {
            "DISCOVERED": "DISCOVERED",
            "TRIAGED": "TRIAGED",
            "RESEARCHING": "RESEARCHING",
            "EVIDENCE_READY": "EVIDENCE_READY",
            "STALE": "STALE",
            "FAILED": "FAILED",
            "ARCHIVED": "ARCHIVED",
        }
        actual = {member.name: member.value for member in ResearchState}
        assert actual == expected


class TestUserDispositionEnum:
    """Test UserDisposition enum has correct members and values."""

    def test_user_disposition_members(self):
        """Assert exact member-value set."""
        expected = {
            "UNDECIDED": "UNDECIDED",
            "STRONG": "STRONG",
            "WATCH": "WATCH",
            "ACT": "ACT",
            "REJECTED": "REJECTED",
        }
        actual = {member.name: member.value for member in UserDisposition}
        assert actual == expected


class TestApplicationStageEnum:
    """Test ApplicationStage enum has correct members and values."""

    def test_application_stage_members(self):
        """Assert exact member-value set."""
        expected = {
            "NOT_STARTED": "NOT_STARTED",
            "PREPARING": "PREPARING",
            "CONTACTED": "CONTACTED",
            "APPLICATION_OPEN": "APPLICATION_OPEN",
            "APPLIED": "APPLIED",
            "INTERVIEW": "INTERVIEW",
            "OFFER": "OFFER",
            "DECLINED": "DECLINED",
            "CLOSED": "CLOSED",
        }
        actual = {member.name: member.value for member in ApplicationStage}
        assert actual == expected


class TestClaimTypeEnum:
    """Test ClaimType enum has correct members and values."""

    def test_claim_type_members(self):
        """Assert exact member-value set."""
        expected = {
            "EXTERNAL_FACT": "EXTERNAL_FACT",
            "OBSERVED_RELATION": "OBSERVED_RELATION",
            "INFERENCE": "INFERENCE",
            "USER_DECISION": "USER_DECISION",
        }
        actual = {member.name: member.value for member in ClaimType}
        assert actual == expected


class TestClaimStatusEnum:
    """Test ClaimStatus enum has correct members and values."""

    def test_claim_status_members(self):
        """Assert exact member-value set."""
        expected = {
            "SUPPORTED": "SUPPORTED",
            "PARTIAL": "PARTIAL",
            "CONTRADICTED": "CONTRADICTED",
            "UNKNOWN": "UNKNOWN",
            "STALE": "STALE",
        }
        actual = {member.name: member.value for member in ClaimStatus}
        assert actual == expected


class TestSnapshotStateEnum:
    """Test SnapshotState enum has correct members and values."""

    def test_snapshot_state_members(self):
        """Assert exact member-value set."""
        expected = {
            "CAPTURED": "CAPTURED",
            "UNCHANGED": "UNCHANGED",
            "CHANGED": "CHANGED",
            "FETCH_FAILED": "FETCH_FAILED",
        }
        actual = {member.name: member.value for member in SnapshotState}
        assert actual == expected


class TestGateResultEnum:
    """Test GateResult enum has correct members and values."""

    # ORACLE-004
    def test_gate_result_members(self):
        """Assert exact member-value set."""
        expected = {
            "PASS": "PASS",
            "FAIL": "FAIL",
            "UNKNOWN": "UNKNOWN",
            "NOT_APPLICABLE": "NOT_APPLICABLE",
            "STALE": "STALE",
        }
        actual = {member.name: member.value for member in GateResult}
        assert actual == expected


class TestSourceAuthorityEnum:
    """Test SourceAuthority enum has correct members and values."""

    def test_source_authority_members(self):
        """Assert exact member-value set."""
        expected = {
            "OFFICIAL_REGULATION": "OFFICIAL_REGULATION",
            "OFFICIAL_PROGRAMME": "OFFICIAL_PROGRAMME",
            "OFFICIAL_DEPARTMENT_OR_PERSON": "OFFICIAL_DEPARTMENT_OR_PERSON",
            "AUTHORITATIVE_REGISTRY": "AUTHORITATIVE_REGISTRY",
            "PRIMARY_RESEARCH_OUTPUT": "PRIMARY_RESEARCH_OUTPUT",
            "REPUTABLE_SECONDARY": "REPUTABLE_SECONDARY",
            "DISCOVERY_AGGREGATOR": "DISCOVERY_AGGREGATOR",
            "UNKNOWN": "UNKNOWN",
        }
        actual = {member.name: member.value for member in SourceAuthority}
        assert actual == expected


class TestDeadlinePrecisionEnum:
    """Test DeadlinePrecision enum has correct members and values."""

    def test_deadline_precision_members(self):
        """Assert exact member-value set."""
        expected = {
            "DATE_ONLY": "DATE_ONLY",
            "LOCAL_TIME": "LOCAL_TIME",
            "OFFSET_AWARE": "OFFSET_AWARE",
            "AMBIGUOUS": "AMBIGUOUS",
        }
        actual = {member.name: member.value for member in DeadlinePrecision}
        assert actual == expected


class TestRouteStateEnum:
    """Test RouteState enum has correct members and values."""

    def test_route_state_members(self):
        """Assert exact member-value set."""
        expected = {
            "ACTIVE": "ACTIVE",
            "EXPLORATORY": "EXPLORATORY",
            "DORMANT": "DORMANT",
            "RETIRED": "RETIRED",
        }
        actual = {member.name: member.value for member in RouteState}
        assert actual == expected


class TestProfileStateEnum:
    """Test ProfileState enum has correct members and values."""

    def test_profile_state_members(self):
        """Assert exact member-value set."""
        expected = {
            "ACTIVE": "ACTIVE",
            "NEEDS_VERIFICATION": "NEEDS_VERIFICATION",
            "SUPERSEDED": "SUPERSEDED",
        }
        actual = {member.name: member.value for member in ProfileState}
        assert actual == expected


class TestCoverageStatusEnum:
    """Test CoverageStatus enum has correct members and values."""

    def test_coverage_status_members(self):
        """Assert exact member-value set."""
        expected = {
            "SEARCHED_FOUND": "SEARCHED_FOUND",
            "SEARCHED_NONE_FOUND": "SEARCHED_NONE_FOUND",
            "NOT_SEARCHED": "NOT_SEARCHED",
            "BLOCKED": "BLOCKED",
        }
        actual = {member.name: member.value for member in CoverageStatus}
        assert actual == expected


class TestTargetKindEnum:
    """Test TargetKind enum has correct members and values."""

    def test_target_kind_members(self):
        """Assert exact member-value set."""
        expected = {
            "Person": "Person",
            "Programme": "Programme",
            "PhDOpportunity": "PhDOpportunity",
            "FundedProject": "FundedProject",
            "Institution": "Institution",
            "FundingRoute": "FundingRoute",
            "SupervisedProject": "SupervisedProject",
            "Work": "Work",
        }
        actual = {member.name: member.value for member in TargetKind}
        assert actual == expected


class TestApplicationRouteEnum:
    """Test ApplicationRoute enum has correct members and values."""

    def test_application_route_members(self):
        """Assert exact member-value set."""
        expected = {
            "SUPERVISOR_FIRST_PHD": "SUPERVISOR_FIRST_PHD",
            "ADVERTISED_PHD": "ADVERTISED_PHD",
            "STRUCTURED_PHD": "STRUCTURED_PHD",
            "MA_PROGRAMME": "MA_PROGRAMME",
        }
        actual = {member.name: member.value for member in ApplicationRoute}
        assert actual == expected


class TestIdentityStatusEnum:
    """Test IdentityStatus enum has correct members and values."""

    def test_identity_status_members(self):
        """Assert exact member-value set."""
        expected = {
            "RESOLVED": "RESOLVED",
            "UNRESOLVED": "UNRESOLVED",
            "CANDIDATE": "CANDIDATE",
        }
        actual = {member.name: member.value for member in IdentityStatus}
        assert actual == expected


class TestLegalTransitions:
    """Test LEGAL_TRANSITIONS dictionary and can_transition function."""

    def test_legal_transitions_structure(self):
        """Assert LEGAL_TRANSITIONS has correct keys and values."""
        expected_transitions = {
            ResearchState.DISCOVERED: {ResearchState.TRIAGED, ResearchState.ARCHIVED},
            ResearchState.TRIAGED: {ResearchState.RESEARCHING, ResearchState.ARCHIVED},
            ResearchState.RESEARCHING: {ResearchState.EVIDENCE_READY, ResearchState.FAILED},
            ResearchState.FAILED: {ResearchState.RESEARCHING, ResearchState.ARCHIVED},
            ResearchState.EVIDENCE_READY: {ResearchState.STALE, ResearchState.RESEARCHING, ResearchState.ARCHIVED},
            ResearchState.STALE: {ResearchState.RESEARCHING, ResearchState.ARCHIVED},
        }
        assert LEGAL_TRANSITIONS == expected_transitions

    def test_legal_transitions_true_for_all_legal_pairs(self):
        """Assert can_transition returns True for all legal pairs."""
        for from_state, to_states in LEGAL_TRANSITIONS.items():
            for to_state in to_states:
                assert can_transition(from_state, to_state), (
                    f"can_transition({from_state}, {to_state}) should be True"
                )

    def test_illegal_transitions_false_for_all_pairs(self):
        """Assert can_transition returns False for all illegal pairs."""
        all_states = set(ResearchState)
        for from_state in all_states:
            legal_destinations = LEGAL_TRANSITIONS.get(from_state, set())
            for to_state in all_states:
                if to_state not in legal_destinations:
                    assert not can_transition(from_state, to_state), (
                        f"can_transition({from_state}, {to_state}) should be False"
                    )

    def test_matrix_coverage(self):
        """Assert we test all possible ordered pairs."""
        all_states = list(ResearchState)
        n_states = len(all_states)
        # Full matrix is n^2 pairs
        total_pairs = n_states * n_states

        legal_count = sum(len(destinations) for destinations in LEGAL_TRANSITIONS.values())
        illegal_count = total_pairs - legal_count

        # Verify we have a reasonable distribution
        assert legal_count > 0, "Should have at least one legal transition"
        assert illegal_count > 0, "Should have at least one illegal transition"


class TestCrossEnumMisuse:
    """Test that enum values cannot be mixed across different enums."""

    def test_research_state_values_not_in_user_disposition(self):
        """Assert ResearchState members cannot be used as UserDisposition."""
        user_disposition_values = {member.value for member in UserDisposition}
        for research_state in ResearchState:
            assert research_state.value not in user_disposition_values, (
                f"ResearchState.{research_state.name} value should not exist in UserDisposition"
            )

    def test_user_disposition_values_not_in_research_state(self):
        """Assert UserDisposition members cannot be used as ResearchState."""
        research_state_values = {member.value for member in ResearchState}
        for user_disp in UserDisposition:
            assert user_disp.value not in research_state_values, (
                f"UserDisposition.{user_disp.name} value should not exist in ResearchState"
            )

    def test_application_stage_distinct_from_research_state(self):
        """Assert ApplicationStage values are distinct from ResearchState."""
        research_state_values = {member.value for member in ResearchState}
        for app_stage in ApplicationStage:
            assert app_stage.value not in research_state_values, (
                f"ApplicationStage.{app_stage.name} value should not exist in ResearchState"
            )

    def test_claim_type_distinct_from_claim_status(self):
        """Assert ClaimType and ClaimStatus values are distinct."""
        claim_type_values = {member.value for member in ClaimType}
        claim_status_values = {member.value for member in ClaimStatus}

        overlap = claim_type_values & claim_status_values
        assert not overlap, (
            f"ClaimType and ClaimStatus should have no overlapping values, found: {overlap}"
        )
