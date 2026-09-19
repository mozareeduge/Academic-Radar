"""Test dimension assessment and summarization."""

import pytest

from academic_radar.domain.dimensions import (
    SupervisorDimension,
    SUPERVISOR_DIMENSIONS,
    MAHead,
    MA_HEADS,
    MAHeadValue,
    assess_dimension,
    summarize_supervisor,
    summarize_ma,
)
from tests.academic_radar.canary import expect_violation


class TestSupervisorDimensions:
    """Test supervisor dimension enum and tuple."""

    def test_supervisor_dimensions_has_seven(self):
        """Assert SUPERVISOR_DIMENSIONS has exactly 7 dimensions."""
        assert len(SUPERVISOR_DIMENSIONS) == 7

    def test_supervisor_dimensions_values(self):
        """Assert all expected dimension values are present."""
        expected = {
            SupervisorDimension.TOPIC_RESONANCE,
            SupervisorDimension.METHOD_ALIGNMENT,
            SupervisorDimension.THEORY_ALIGNMENT,
            SupervisorDimension.TRACK_B_PRACTICE_OPENNESS,
            SupervisorDimension.ECOSYSTEM_INFRASTRUCTURE,
            SupervisorDimension.SUPERVISION_CAPACITY,
            SupervisorDimension.FUNDING_PLAUSIBILITY,
        }
        assert set(SUPERVISOR_DIMENSIONS) == expected


class TestMAHeads:
    """Test MA assessment heads."""

    def test_ma_heads_has_three(self):
        """Assert MA_HEADS has exactly 3 heads."""
        assert len(MA_HEADS) == 3

    def test_ma_heads_values(self):
        """Assert all expected head values are present."""
        expected = {
            MAHead.ADMISSION_VIABILITY,
            MAHead.FUNDING_VIABILITY,
            MAHead.STRATEGIC_VALUE,
        }
        assert set(MA_HEADS) == expected


class TestAssessDimension:
    """Test assess_dimension function."""

    def test_none_value_no_evidence_allowed(self):
        """Assert None value can have empty evidence_ids."""
        result = assess_dimension(
            SupervisorDimension.TOPIC_RESONANCE,
            None,
            [],
            ["missing supervisor info"],
        )
        assert result["value"] is None
        assert result["evidence_ids"] == []
        assert "missing supervisor info" in result["unknowns"]

    def test_none_value_stays_none(self):
        """Assert None values are preserved, not converted to 0."""
        result = assess_dimension(
            SupervisorDimension.METHOD_ALIGNMENT,
            None,
            [],
            [],
        )
        assert result["value"] is None
        assert result["value"] != 0

    def test_value_0_requires_evidence(self):
        """Assert value 0 (not None) requires evidence_ids."""
        with pytest.raises(ValueError, match="non-None value requires evidence_ids"):
            assess_dimension(
                SupervisorDimension.THEORY_ALIGNMENT,
                0,
                [],
                [],
            )

    def test_value_3_requires_evidence(self):
        """Assert value 3 requires evidence_ids."""
        with pytest.raises(ValueError, match="non-None value requires evidence_ids"):
            assess_dimension(
                SupervisorDimension.FUNDING_PLAUSIBILITY,
                3,
                [],
                [],
            )

    def test_value_4_raises(self):
        """Assert value 4 raises ValueError."""
        with pytest.raises(ValueError, match="value must be None or int 0-3"):
            assess_dimension(
                SupervisorDimension.TOPIC_RESONANCE,
                4,
                ["ev1"],
                [],
            )

    def test_value_negative_raises(self):
        """Assert negative values raise ValueError."""
        with pytest.raises(ValueError, match="value must be None or int 0-3"):
            assess_dimension(
                SupervisorDimension.METHOD_ALIGNMENT,
                -1,
                ["ev1"],
                [],
            )

    def test_value_with_evidence_succeeds(self):
        """Assert valid value and evidence_ids succeed."""
        result = assess_dimension(
            SupervisorDimension.ECOSYSTEM_INFRASTRUCTURE,
            2,
            ["ev1", "ev2"],
            ["potential gap in funding models"],
        )
        assert result["value"] == 2
        assert result["evidence_ids"] == ["ev1", "ev2"]

    def test_returns_dict_with_all_keys(self):
        """Assert returned dict has dimension, value, evidence_ids, unknowns."""
        result = assess_dimension(
            SupervisorDimension.SUPERVISION_CAPACITY,
            1,
            ["ev1"],
            ["workload"],
        )
        assert "dimension" in result
        assert "value" in result
        assert "evidence_ids" in result
        assert "unknowns" in result


class TestSummarizeSupervisor:
    """Test summarize_supervisor function."""

    def test_supervisor_summary_has_no_score_key(self):
        """Assert summary has no 'score' key."""
        assessments = [
            assess_dimension(SupervisorDimension.TOPIC_RESONANCE, 2, ["ev1"], []),
        ]
        result = summarize_supervisor(assessments)
        assert "score" not in result
        assert "total" not in result

    def test_supervisor_summary_has_no_total_key(self):
        """Assert summary has no 'total' key."""
        assessments = [
            assess_dimension(SupervisorDimension.METHOD_ALIGNMENT, 3, ["ev1"], []),
        ]
        result = summarize_supervisor(assessments)
        assert "total" not in result

    def test_supervisor_summary_has_no_overall_key(self):
        """Assert summary has no 'overall' key."""
        assessments = [
            assess_dimension(SupervisorDimension.THEORY_ALIGNMENT, 1, ["ev1"], []),
        ]
        result = summarize_supervisor(assessments)
        assert "overall" not in result

    def test_supervisor_summary_has_no_average_key(self):
        """Assert summary has no 'average' key."""
        assessments = [
            assess_dimension(SupervisorDimension.TRACK_B_PRACTICE_OPENNESS, 2, ["ev1"], []),
        ]
        result = summarize_supervisor(assessments)
        assert "average" not in result

    def test_supervisor_summary_has_fit_key(self):
        """Assert summary has no 'fit' key."""
        assessments = [
            assess_dimension(SupervisorDimension.ECOSYSTEM_INFRASTRUCTURE, 0, ["ev1"], []),
        ]
        result = summarize_supervisor(assessments)
        assert "fit" not in result

    def test_supervisor_summary_has_unknown_dims_list(self):
        """Assert summary has unknown_dims list."""
        assessments = [
            assess_dimension(SupervisorDimension.SUPERVISION_CAPACITY, 2, ["ev1"], []),
            assess_dimension(SupervisorDimension.FUNDING_PLAUSIBILITY, None, [], ["unknown"]),
        ]
        result = summarize_supervisor(assessments)
        assert "unknown_dims" in result
        assert isinstance(result["unknown_dims"], list)

    def test_supervisor_summary_tracks_unknown_dimensions(self):
        """Assert None values are tracked in unknown_dims."""
        assessments = [
            assess_dimension(SupervisorDimension.TOPIC_RESONANCE, 2, ["ev1"], []),
            assess_dimension(SupervisorDimension.METHOD_ALIGNMENT, None, [], ["missing data"]),
            assess_dimension(SupervisorDimension.THEORY_ALIGNMENT, 1, ["ev2"], []),
        ]
        result = summarize_supervisor(assessments)
        assert SupervisorDimension.METHOD_ALIGNMENT in result["unknown_dims"]
        assert SupervisorDimension.TOPIC_RESONANCE not in result["unknown_dims"]

    def test_supervisor_summary_includes_dimension_values(self):
        """Assert summary includes dimension as key with value."""
        dim = SupervisorDimension.TRACK_B_PRACTICE_OPENNESS
        assessments = [assess_dimension(dim, 3, ["ev1"], [])]
        result = summarize_supervisor(assessments)
        assert result[dim] == 3

    def test_supervisor_summary_preserves_none(self):
        """Assert None values are preserved in summary."""
        dim = SupervisorDimension.ECOSYSTEM_INFRASTRUCTURE
        assessments = [assess_dimension(dim, None, [], [])]
        result = summarize_supervisor(assessments)
        assert result[dim] is None


class TestSummarizeMA:
    """Test summarize_ma function."""

    def test_ma_summary_has_no_combined_key(self):
        """Assert MA summary has no 'combined' key."""
        heads = [
            {
                "head": MAHead.ADMISSION_VIABILITY,
                "value": MAHeadValue.STRONG,
                "evidence_ids": ["ev1"],
                "unknowns": [],
            }
        ]
        result = summarize_ma(heads)
        assert "combined" not in result
        assert "fit" not in result

    def test_ma_summary_has_exactly_three_head_keys(self):
        """Assert MA summary has each head as a key."""
        heads = [
            {
                "head": MAHead.ADMISSION_VIABILITY,
                "value": MAHeadValue.STRONG,
                "evidence_ids": ["ev1"],
                "unknowns": [],
            },
            {
                "head": MAHead.FUNDING_VIABILITY,
                "value": MAHeadValue.MIXED,
                "evidence_ids": ["ev2"],
                "unknowns": [],
            },
            {
                "head": MAHead.STRATEGIC_VALUE,
                "value": MAHeadValue.WEAK,
                "evidence_ids": ["ev3"],
                "unknowns": [],
            },
        ]
        result = summarize_ma(heads)
        assert MAHead.ADMISSION_VIABILITY in result
        assert MAHead.FUNDING_VIABILITY in result
        assert MAHead.STRATEGIC_VALUE in result

    def test_ma_summary_has_evidence_ids_list(self):
        """Assert MA summary has evidence_ids list."""
        heads = [
            {
                "head": MAHead.ADMISSION_VIABILITY,
                "value": MAHeadValue.UNKNOWN,
                "evidence_ids": ["ev1"],
                "unknowns": [],
            }
        ]
        result = summarize_ma(heads)
        assert "evidence_ids" in result
        assert isinstance(result["evidence_ids"], list)

    def test_ma_summary_has_unknowns_list(self):
        """Assert MA summary has unknowns list."""
        heads = [
            {
                "head": MAHead.FUNDING_VIABILITY,
                "value": MAHeadValue.STRONG,
                "evidence_ids": ["ev1"],
                "unknowns": ["scholarship details"],
            }
        ]
        result = summarize_ma(heads)
        assert "unknowns" in result
        assert isinstance(result["unknowns"], list)

    def test_ma_summary_aggregates_evidence_ids(self):
        """Assert evidence_ids from all heads are aggregated."""
        heads = [
            {
                "head": MAHead.ADMISSION_VIABILITY,
                "value": MAHeadValue.STRONG,
                "evidence_ids": ["ev1", "ev2"],
                "unknowns": [],
            },
            {
                "head": MAHead.FUNDING_VIABILITY,
                "value": MAHeadValue.MIXED,
                "evidence_ids": ["ev3"],
                "unknowns": [],
            },
        ]
        result = summarize_ma(heads)
        assert set(result["evidence_ids"]) == {"ev1", "ev2", "ev3"}

    def test_ma_summary_aggregates_unknowns(self):
        """Assert unknowns from all heads are aggregated."""
        heads = [
            {
                "head": MAHead.ADMISSION_VIABILITY,
                "value": MAHeadValue.STRONG,
                "evidence_ids": ["ev1"],
                "unknowns": ["language requirement"],
            },
            {
                "head": MAHead.STRATEGIC_VALUE,
                "value": MAHeadValue.WEAK,
                "evidence_ids": ["ev2"],
                "unknowns": ["career alignment"],
            },
        ]
        result = summarize_ma(heads)
        assert "language requirement" in result["unknowns"]
        assert "career alignment" in result["unknowns"]


@pytest.mark.canary
def test_canary_no_universal_score():
    """Canary: detect if summarize_supervisor adds an 'overall' key."""
    def mutated_summarize_supervisor(assessments):
        result = summarize_supervisor(assessments)
        result["overall"] = 2
        return result

    assessments = [
        assess_dimension(SupervisorDimension.TOPIC_RESONANCE, 2, ["ev1"], []),
    ]

    def check_no_overall():
        result = mutated_summarize_supervisor(assessments)
        assert "overall" not in result

    expect_violation(check_no_overall)
