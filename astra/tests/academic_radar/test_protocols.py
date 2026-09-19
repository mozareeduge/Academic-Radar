import pytest
from academic_radar.domain.protocols import Protocol, Readiness, compute_readiness
from academic_radar.domain.enums import CoverageStatus
from tests.academic_radar.canary import expect_violation


class TestComputeReadiness:
    """Test protocol readiness computation (ORACLE-008, ORACLE-009)."""

    def test_all_mandatory_found(self):
        """All mandatory classes SEARCHED_FOUND => ready."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine", "publications"),
            optional=("grant_history",),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30, "publications": 60},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.SEARCHED_FOUND,
            "publications": CoverageStatus.SEARCHED_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is True
        assert result.missing == []
        assert result.blocked == []
        assert result.partial is False

    def test_one_mandatory_not_searched(self):
        """One mandatory class NOT_SEARCHED => not ready, listed in missing."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine", "publications"),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30, "publications": 60},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.NOT_SEARCHED,
            "publications": CoverageStatus.SEARCHED_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is False
        assert "supervisor_spine" in result.missing
        assert result.blocked == []

    def test_zero_result_with_allow_zero_result_true(self):
        """Zero-result search with allow_zero_result=True => counts as ready."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine",),
            optional=(),
            allow_zero_result=True,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.SEARCHED_NONE_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is True
        assert result.missing == []

    def test_zero_result_with_allow_zero_result_false(self):
        """Zero-result search with allow_zero_result=False => not ready."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine",),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.SEARCHED_NONE_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is False
        assert "supervisor_spine" in result.missing

    def test_mandatory_blocked(self):
        """Mandatory class BLOCKED => listed in blocked, not ready."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine", "publications"),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30, "publications": 60},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.BLOCKED,
            "publications": CoverageStatus.SEARCHED_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is False
        assert "supervisor_spine" in result.blocked
        assert "supervisor_spine" not in result.missing

    def test_missing_key_in_coverage_treated_as_not_searched(self):
        """Missing key in coverage dict => treated as NOT_SEARCHED."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine", "publications"),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30, "publications": 60},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.SEARCHED_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is False
        assert "publications" in result.missing

    def test_optional_classes_not_checked(self):
        """Optional classes are not checked for readiness."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine",),
            optional=("grant_history",),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.SEARCHED_FOUND,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is True

    def test_partial_flag_set_when_not_ready(self):
        """When not ready, partial flag reflects incomplete status."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_spine", "publications"),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_spine": 30, "publications": 60},
        )
        coverage = {
            "supervisor_spine": CoverageStatus.SEARCHED_FOUND,
            "publications": CoverageStatus.NOT_SEARCHED,
        }
        result = compute_readiness(protocol, coverage)
        assert result.ready is False
        assert result.partial is True


@pytest.mark.canary
def test_canary_missing_mandatory_class():
    """Canary: detect missing mandatory class via mutated compute_readiness.

    This test exercises the expect_violation pattern: a mutated version
    that reads an extra model_says_complete flag must be caught as a failure.
    When model_says_complete=True is passed to the mutated function,
    it incorrectly skips the NOT_SEARCHED check and returns ready=True.
    """
    def compute_readiness_mutated(protocol, coverage: dict, model_says_complete=False):
        """MUTATED: honors model_says_complete flag, violating requirement."""
        for mandatory_class in protocol.mandatory:
            status = coverage.get(mandatory_class, CoverageStatus.NOT_SEARCHED)
            if status == CoverageStatus.BLOCKED:
                continue
            if status == CoverageStatus.SEARCHED_FOUND:
                continue
            if status == CoverageStatus.SEARCHED_NONE_FOUND and protocol.allow_zero_result:
                continue
            if model_says_complete:
                continue
            return False
        return True

    protocol = Protocol(
        application_route="MA_PROGRAMME",
        version="1.0",
        mandatory=("supervisor_spine",),
        optional=(),
        allow_zero_result=False,
        allowed_unknowns=(),
        blocking_unknowns=(),
        freshness_days={"supervisor_spine": 30},
    )
    coverage = {
        "supervisor_spine": CoverageStatus.NOT_SEARCHED,
    }

    def check_assert_not_ready():
        result_ready = compute_readiness_mutated(protocol, coverage, model_says_complete=True)
        assert not result_ready

    expect_violation(check_assert_not_ready)
