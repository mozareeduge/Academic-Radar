"""Research protocol engine and readiness computation.

OBJ-014: ResearchProtocol with mandatory/optional evidence classes,
freshness rules, allowed/blocking unknowns.
DEC-036: Research completion is protocol-based; model narrative
completion is not completion.
ORACLE-008: EVIDENCE_READY requires every mandatory evidence class
to be completed or explicitly recorded as allowed unknown.
ORACLE-009: Protocol coverage distinguishes searched-with-zero-evidence
from not-yet-searched evidence class.
"""

from dataclasses import dataclass
from academic_radar.domain.enums import CoverageStatus


@dataclass(frozen=True)
class Protocol:
    """Versioned route-specific specification controlling deep research."""

    application_route: str
    version: str
    mandatory: tuple[str, ...]
    optional: tuple[str, ...]
    allow_zero_result: bool
    allowed_unknowns: tuple[str, ...]
    blocking_unknowns: tuple[str, ...]
    freshness_days: dict[str, int]


@dataclass(frozen=True)
class Readiness:
    """Result of protocol readiness computation."""

    ready: bool
    missing: list[str]
    blocked: list[str]
    partial: bool


def compute_readiness(protocol: Protocol, coverage: dict[str, CoverageStatus]) -> Readiness:
    """Compute protocol readiness based on coverage status.

    ready is True ONLY when every mandatory class is SEARCHED_FOUND,
    or SEARCHED_NONE_FOUND while protocol.allow_zero_result is True.

    NOT_SEARCHED or BLOCKED on any mandatory class => ready False
    and listed in missing/blocked respectively.

    Missing key in coverage is treated as NOT_SEARCHED.
    """
    missing = []
    blocked = []

    for mandatory_class in protocol.mandatory:
        status = coverage.get(mandatory_class, CoverageStatus.NOT_SEARCHED)

        if status == CoverageStatus.BLOCKED:
            blocked.append(mandatory_class)
        elif status == CoverageStatus.SEARCHED_FOUND:
            continue
        elif status == CoverageStatus.SEARCHED_NONE_FOUND:
            if protocol.allow_zero_result:
                continue
            missing.append(mandatory_class)
        elif status == CoverageStatus.NOT_SEARCHED:
            missing.append(mandatory_class)

    ready = len(missing) == 0 and len(blocked) == 0
    partial = not ready

    return Readiness(ready=ready, missing=missing, blocked=blocked, partial=partial)
