"""Authority-based conflict resolution for evidence statements.

DEC-037: Source authority is explicit
Official current programme/funder rules govern formal gates over aggregators/secondary
summaries unless authority/freshness is unresolved.

DEC-038: Copied evidence is not independent evidence
Evidence stores canonical-origin grouping; repeated syndication cannot inflate corroboration
strength.

ORACLE-014: Source authority governs formal rules
Current official programme/funder/university rules outrank discovery aggregators and
secondary summaries for formal gates unless official authority/freshness is itself unresolved.

ORACLE-015: Repeated sources do not fake corroboration
Syndicated/copied statements sharing canonical origin count as one upstream assertion.

ORACLE-016: Contradiction remains visible
Unresolved contradictory evidence is stored/displayed as contradiction rather than
arbitrarily resolved.
"""

from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass
from academic_radar.domain.enums import SourceAuthority


@dataclass
class ConflictResolution:
    """Result of resolving conflicting statements."""
    status: str
    winner_value: Optional[Any]
    winner_authority: Optional[SourceAuthority]
    overridden: list[dict[str, Any]]
    contradicting_values: Optional[list[Any]]


AUTHORITY_HIERARCHY = [
    SourceAuthority.OFFICIAL_REGULATION,
    SourceAuthority.OFFICIAL_PROGRAMME,
    SourceAuthority.OFFICIAL_DEPARTMENT_OR_PERSON,
    SourceAuthority.AUTHORITATIVE_REGISTRY,
    SourceAuthority.PRIMARY_RESEARCH_OUTPUT,
    SourceAuthority.REPUTABLE_SECONDARY,
    SourceAuthority.DISCOVERY_AGGREGATOR,
    SourceAuthority.UNKNOWN,
]


def independent_support_count(artifacts: list[dict[str, Any]]) -> int:
    """Count the number of distinct canonical_origin values in artifacts.

    Mirrors (multiple artifacts with the same canonical_origin) count as one
    independent support, implementing DEC-038 and ORACLE-015.

    Args:
        artifacts: list of artifact dicts, each with canonical_origin key

    Returns:
        count of unique canonical_origin values
    """
    if not artifacts:
        return 0
    origins = {artifact["canonical_origin"] for artifact in artifacts}
    return len(origins)


def resolve_conflict(
    statements: list[dict[str, Any]],
) -> ConflictResolution:
    """Resolve conflicting statements by authority hierarchy.

    Implements ORACLE-014 (authority governs formal rules) and ORACLE-016
    (contradictions remain visible).

    Authority precedence (highest to lowest):
    1. OFFICIAL_REGULATION
    2. OFFICIAL_PROGRAMME
    3. OFFICIAL_DEPARTMENT_OR_PERSON
    4. AUTHORITATIVE_REGISTRY
    5. PRIMARY_RESEARCH_OUTPUT
    6. REPUTABLE_SECONDARY
    7. DISCOVERY_AGGREGATOR
    8. UNKNOWN

    Resolution logic:
    - If statements have same value: return RESOLVED with that value
    - If highest-authority statements disagree: return CONTRADICTED with no winner
    - Otherwise: return RESOLVED with highest-authority value, others marked overridden

    Args:
        statements: list of dicts with keys:
            - value: the claim value
            - authority: SourceAuthority enum
            - effective_date: datetime of when the statement was effective

    Returns:
        ConflictResolution with status, winner, overridden list, and contradicting_values
    """
    if not statements:
        return ConflictResolution(
            status="RESOLVED",
            winner_value=None,
            winner_authority=None,
            overridden=[],
            contradicting_values=None,
        )

    if len(statements) == 1:
        stmt = statements[0]
        return ConflictResolution(
            status="RESOLVED",
            winner_value=stmt["value"],
            winner_authority=stmt["authority"],
            overridden=[],
            contradicting_values=None,
        )

    # Find the highest authority level present in statements
    top_authority = None
    for auth in AUTHORITY_HIERARCHY:
        if any(stmt["authority"] == auth for stmt in statements):
            top_authority = auth
            break

    # Filter statements to only those with the top authority
    top_authority_statements = [
        stmt for stmt in statements if stmt["authority"] == top_authority
    ]

    # Check if top-authority statements have conflicting values
    top_values = set(str(stmt["value"]) for stmt in top_authority_statements)

    if len(top_values) > 1:
        # Contradiction among top-authority statements
        return ConflictResolution(
            status="CONTRADICTED",
            winner_value=None,
            winner_authority=None,
            overridden=[],
            contradicting_values=[stmt["value"] for stmt in top_authority_statements],
        )

    # All top-authority statements agree; pick one as winner (any will have same value)
    winner = top_authority_statements[0]

    # Mark all non-winner statements as overridden (including duplicates at same authority)
    overridden = [
        {
            "value": stmt["value"],
            "authority": stmt["authority"],
            "effective_date": stmt.get("effective_date"),
        }
        for i, stmt in enumerate(statements)
        if i != statements.index(winner)
    ]

    return ConflictResolution(
        status="RESOLVED",
        winner_value=winner["value"],
        winner_authority=winner["authority"],
        overridden=overridden,
        contradicting_values=None,
    )
