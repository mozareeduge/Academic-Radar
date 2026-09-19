"""Freshness assessment for external evidence facts.

DEC-028: Each consequential external fact exposes last checked. Stale critical
facts are visually elevated before action/application brief freeze.
ORACLE-028: System tracks freshness of evidence and marks stale critical facts.
"""

from datetime import datetime, timezone
from academic_radar.domain.protocols import Protocol


def is_stale(last_checked_at: datetime, evidence_class: str, protocol: Protocol, now: datetime) -> bool:
    """Check if evidence is stale based on protocol freshness rules.

    Args:
        last_checked_at: When the evidence was last checked/fetched
        evidence_class: The evidence class name to look up freshness rule
        protocol: The protocol defining freshness_days rules
        now: Current timestamp for comparison

    Returns:
        True if the evidence is older than the protocol's freshness_days threshold.
        False if freshness_days is not defined for the evidence class.
    """
    if evidence_class not in protocol.freshness_days:
        return False

    freshness_days = protocol.freshness_days[evidence_class]
    if freshness_days is None:
        return False

    elapsed_seconds = (now - last_checked_at).total_seconds()
    elapsed_days = elapsed_seconds / (24 * 3600)

    return elapsed_days > freshness_days
