"""Gate assessment and hard-blocker logic."""

from dataclasses import dataclass

from academic_radar.domain.enums import GateResult


@dataclass
class Gate:
    """Formal gate assessment: yes/no/unknown evaluation of a requirement."""

    name: str
    hard: bool
    result: GateResult
    evidence_ids: list[str]


def validate_gate(gate: Gate) -> None:
    """Validate that a gate has required evidence for its result type.

    PASS and FAIL results require at least one evidence id.
    UNKNOWN, NOT_APPLICABLE, and STALE require none.

    Raises ValueError if evidence requirements are not met.
    """
    if gate.result in (GateResult.PASS, GateResult.FAIL):
        if not gate.evidence_ids:
            raise ValueError(
                f"Gate {gate.name} with result {gate.result.value} "
                "must have at least one evidence id"
            )


def blockers(gates: list[Gate]) -> list[Gate]:
    """Return hard gates with FAIL result.

    These represent formal blockers that prevent actionability.
    """
    return [g for g in gates if g.hard and g.result == GateResult.FAIL]


def unknowns(gates: list[Gate]) -> list[Gate]:
    """Return all gates with UNKNOWN result, kept distinct from FAIL.

    Unknown gates may be hard or soft. This represents missing evidence,
    not a failure of eligibility.
    """
    return [g for g in gates if g.result == GateResult.UNKNOWN]


def actionable(gates: list[Gate]) -> bool:
    """True only if no hard gate has a FAIL result.

    A formal blocker makes the case non-actionable regardless of
    intellectual fit or other factors. The function takes no fit argument.
    """
    return len(blockers(gates)) == 0


def formally_open(gates: list[Gate]) -> bool:
    """True only when no hard gate has FAIL and no hard gate has UNKNOWN.

    Hard gates determine formal eligibility. Soft gates do not affect
    this determination. NOT_APPLICABLE, PASS, and other results
    do not prevent formally_open from being True.
    """
    hard_gates = [g for g in gates if g.hard]
    for g in hard_gates:
        if g.result == GateResult.FAIL or g.result == GateResult.UNKNOWN:
            return False
    return True
