import pytest
from datetime import datetime, timezone
from academic_radar.evidence.authority_logic import (
    independent_support_count,
    resolve_conflict,
    ConflictResolution,
)
from academic_radar.domain.enums import SourceAuthority
from tests.academic_radar.canary import expect_violation


class TestIndependentSupportCount:
    """Test counting distinct canonical_origin values (mirrors count once)."""

    # ORACLE-015
    def test_single_artifact(self):
        """Single artifact counts as 1."""
        artifacts = [
            {"canonical_origin": "origin_abc123"}
        ]
        assert independent_support_count(artifacts) == 1

    def test_three_mirrors_same_origin(self):
        """Three artifacts with identical canonical_origin count as 1."""
        artifacts = [
            {"canonical_origin": "origin_abc123"},
            {"canonical_origin": "origin_abc123"},
            {"canonical_origin": "origin_abc123"},
        ]
        assert independent_support_count(artifacts) == 1

    def test_three_distinct_origins(self):
        """Three artifacts with different canonical_origin count as 3."""
        artifacts = [
            {"canonical_origin": "origin_abc123"},
            {"canonical_origin": "origin_def456"},
            {"canonical_origin": "origin_ghi789"},
        ]
        assert independent_support_count(artifacts) == 3

    def test_mixed_mirrors_and_distinct(self):
        """Two mirrors plus two other distinct origins count as 3."""
        artifacts = [
            {"canonical_origin": "origin_abc123"},
            {"canonical_origin": "origin_abc123"},
            {"canonical_origin": "origin_def456"},
            {"canonical_origin": "origin_ghi789"},
        ]
        assert independent_support_count(artifacts) == 3

    def test_empty_list(self):
        """Empty artifact list counts as 0."""
        artifacts = []
        assert independent_support_count(artifacts) == 0


class TestResolveConflict:
    """Test conflict resolution by authority hierarchy."""

    # ORACLE-014
    def test_official_programme_beats_aggregator(self):
        """Official programme (15 Jan) should beat discovery aggregator (1 Feb)."""
        statements = [
            {
                "value": "2025-02-01",
                "authority": SourceAuthority.DISCOVERY_AGGREGATOR,
                "effective_date": datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "2025-01-15",
                "authority": SourceAuthority.OFFICIAL_PROGRAMME,
                "effective_date": datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        result = resolve_conflict(statements)

        assert result.status == "RESOLVED"
        assert result.winner_value == "2025-01-15"
        assert result.winner_authority == SourceAuthority.OFFICIAL_PROGRAMME
        assert len(result.overridden) == 1
        assert result.overridden[0]["value"] == "2025-02-01"
        assert result.overridden[0]["authority"] == SourceAuthority.DISCOVERY_AGGREGATOR

    # ORACLE-016
    def test_two_official_pages_disagree_contradicted(self):
        """Two OFFICIAL_PROGRAMME statements with different values -> CONTRADICTED."""
        statements = [
            {
                "value": "2025-01-15",
                "authority": SourceAuthority.OFFICIAL_PROGRAMME,
                "effective_date": datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "2025-01-20",
                "authority": SourceAuthority.OFFICIAL_PROGRAMME,
                "effective_date": datetime(2025, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        result = resolve_conflict(statements)

        assert result.status == "CONTRADICTED"
        assert result.winner_value is None
        assert result.winner_authority is None
        assert len(result.contradicting_values) == 2
        assert "2025-01-15" in result.contradicting_values
        assert "2025-01-20" in result.contradicting_values

    def test_same_authority_same_value_resolved(self):
        """Two statements of same authority with same value -> RESOLVED."""
        statements = [
            {
                "value": "2025-01-15",
                "authority": SourceAuthority.OFFICIAL_PROGRAMME,
                "effective_date": datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "2025-01-15",
                "authority": SourceAuthority.OFFICIAL_PROGRAMME,
                "effective_date": datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            },
        ]
        result = resolve_conflict(statements)

        assert result.status == "RESOLVED"
        assert result.winner_value == "2025-01-15"
        assert result.winner_authority == SourceAuthority.OFFICIAL_PROGRAMME
        assert len(result.overridden) == 1

    def test_official_regulation_beats_all(self):
        """OFFICIAL_REGULATION has highest precedence."""
        statements = [
            {
                "value": "no",
                "authority": SourceAuthority.OFFICIAL_REGULATION,
                "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "yes",
                "authority": SourceAuthority.OFFICIAL_PROGRAMME,
                "effective_date": datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "yes",
                "authority": SourceAuthority.DISCOVERY_AGGREGATOR,
                "effective_date": datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        result = resolve_conflict(statements)

        assert result.status == "RESOLVED"
        assert result.winner_value == "no"
        assert result.winner_authority == SourceAuthority.OFFICIAL_REGULATION
        assert len(result.overridden) == 2

    def test_authoritative_registry_beats_aggregator(self):
        """AUTHORITATIVE_REGISTRY beats DISCOVERY_AGGREGATOR."""
        statements = [
            {
                "value": "Dr. Smith",
                "authority": SourceAuthority.DISCOVERY_AGGREGATOR,
                "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "Prof. Dr. Smith",
                "authority": SourceAuthority.AUTHORITATIVE_REGISTRY,
                "effective_date": datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        result = resolve_conflict(statements)

        assert result.status == "RESOLVED"
        assert result.winner_value == "Prof. Dr. Smith"
        assert result.winner_authority == SourceAuthority.AUTHORITATIVE_REGISTRY

    def test_single_statement_resolved(self):
        """Single statement with no conflict -> RESOLVED."""
        statements = [
            {
                "value": "2025-01-15",
                "authority": SourceAuthority.DISCOVERY_AGGREGATOR,
                "effective_date": datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
            }
        ]
        result = resolve_conflict(statements)

        assert result.status == "RESOLVED"
        assert result.winner_value == "2025-01-15"
        assert result.winner_authority == SourceAuthority.DISCOVERY_AGGREGATOR
        assert len(result.overridden) == 0

    def test_lower_authority_newer_date_loses_to_higher_authority(self):
        """Higher authority wins even if older; date does not override authority."""
        statements = [
            {
                "value": "old_value",
                "authority": SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON,
                "effective_date": datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
            {
                "value": "new_value",
                "authority": SourceAuthority.DISCOVERY_AGGREGATOR,
                "effective_date": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            },
        ]
        result = resolve_conflict(statements)

        assert result.status == "RESOLVED"
        assert result.winner_value == "old_value"
        assert result.winner_authority == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
        assert len(result.overridden) == 1
        assert result.overridden[0]["value"] == "new_value"


class TestConflictResolutionState:
    """Test ConflictResolution data structure."""

    def test_resolved_state_has_winner(self):
        """Resolved state must have winner_value and winner_authority."""
        result = ConflictResolution(
            status="RESOLVED",
            winner_value="value1",
            winner_authority=SourceAuthority.OFFICIAL_PROGRAMME,
            overridden=[],
            contradicting_values=None,
        )
        assert result.winner_value == "value1"
        assert result.winner_authority == SourceAuthority.OFFICIAL_PROGRAMME

    def test_contradicted_state_no_winner(self):
        """Contradicted state must have None winner and contradicting_values."""
        result = ConflictResolution(
            status="CONTRADICTED",
            winner_value=None,
            winner_authority=None,
            overridden=[],
            contradicting_values=["val1", "val2"],
        )
        assert result.winner_value is None
        assert result.winner_authority is None
        assert "val1" in result.contradicting_values


@pytest.mark.canary
def test_canary_secondary_source_conflict():
    """Mutation canary: detect if resolve_conflict prefers newest over authority.

    This test catches mutations where resolve_conflict incorrectly prioritizes
    the newest (highest effective_date) statement regardless of authority level.
    OFFICIAL_DEPARTMENT_OR_PERSON must beat DISCOVERY_AGGREGATOR even when the
    aggregator value is much newer.

    Correct behavior: OFFICIAL_DEPARTMENT_OR_PERSON should win (higher authority).
    Mutated behavior: DISCOVERY_AGGREGATOR would win (newer date).
    """
    statements = [
        {
            "value": "aggregator_value",
            "authority": SourceAuthority.DISCOVERY_AGGREGATOR,
            "effective_date": datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "value": "official_value",
            "authority": SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON,
            "effective_date": datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
    ]
    result = resolve_conflict(statements)

    assert result.status == "RESOLVED"
    assert result.winner_value == "official_value"
    assert result.winner_authority == SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON
