"""Suggestion derivation from case facts and gates.

DEC-041: Suggestions are deterministic downstream summaries. The LLM creates
claims/interpretations; a transparent rule layer derives suggested_disposition.
The user alone sets user_disposition.

DEC-029: System may derive a suggestion from explicit rules/evidence but must
show the reasons and uncertainty.

DEC-030: Do not use probability labels without real base-rate evidence. Prefer
formally strong, intellectually strong, funding weak, eligibility uncertain, etc.
"""

from dataclasses import dataclass
from academic_radar.domain.enums import UserDisposition


@dataclass
class Suggestion:
    """Deterministic suggestion derived from case facts."""

    value: UserDisposition
    reasons: list[str]
    uncertainties: list[str]


def suggest(case_facts: dict) -> Suggestion:
    """Derive suggested disposition from case facts.

    Pure, deterministic function with no database or session parameter.

    Input: case_facts dict with:
      - hard_blockers: list[Gate] with FAIL result
      - unknown_hard_gates: list[Gate] with UNKNOWN result
      - deadline_urgency: 'critical' (≤7d), 'high' (≤30d), or None
      - stale_critical_facts: list[str] of evidence classes
      - dimension_unknowns: list[str] of unknown dimension names

    Returns Suggestion with:
      - value: STRONG, WATCH, ACT, REJECTED, or UNDECIDED
      - reasons: list of reasoning strings (no probability words)
      - uncertainties: list of unresolved factors

    Logic:
      - Hard FAIL blockers => REJECTED with reason 'formal blocker'
      - Unknown hard gates => WATCH with reason 'eligibility uncertain'
      - Critical deadline (≤7d) and no blockers => ACT
      - High deadline (≤30d) and no blockers => WATCH
      - Stale critical facts => WATCH with reason including evidence class
      - Dimension unknowns => add to uncertainties
    """
    reasons = []
    uncertainties = []
    blockers = case_facts.get("hard_blockers", [])
    unknown_gates = case_facts.get("unknown_hard_gates", [])
    deadline_urgency = case_facts.get("deadline_urgency")
    stale_critical = case_facts.get("stale_critical_facts", [])
    dim_unknowns = case_facts.get("dimension_unknowns", [])

    if blockers:
        return Suggestion(
            value=UserDisposition.REJECTED,
            reasons=["formal blocker"],
            uncertainties=[]
        )

    if unknown_gates:
        return Suggestion(
            value=UserDisposition.WATCH,
            reasons=["eligibility uncertain"],
            uncertainties=[f"unknown gate: {g.name}" for g in unknown_gates]
        )

    if stale_critical:
        for evidence_class in stale_critical:
            reasons.append(f"stale critical fact: {evidence_class}")

    if dim_unknowns:
        for dim in dim_unknowns:
            uncertainties.append(f"dimension unknown: {dim}")

    if deadline_urgency == "critical":
        if not reasons and not uncertainties:
            reasons.append("deadline ≤7 days")
        return Suggestion(value=UserDisposition.ACT, reasons=reasons, uncertainties=uncertainties)

    if deadline_urgency == "high":
        if not reasons and not uncertainties:
            reasons.append("deadline ≤30 days")
        return Suggestion(value=UserDisposition.WATCH, reasons=reasons, uncertainties=uncertainties)

    if reasons or uncertainties:
        return Suggestion(value=UserDisposition.WATCH, reasons=reasons, uncertainties=uncertainties)

    return Suggestion(value=UserDisposition.UNDECIDED, reasons=[], uncertainties=[])
