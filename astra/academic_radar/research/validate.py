import json
from pydantic import ValidationError
from typing import Optional
from academic_radar.research.schemas.nodes import NodeOutput, ClaimOut
from academic_radar.domain.enums import ClaimType, CoverageStatus


class AcceptResult:
    def __init__(self, accepted: Optional[NodeOutput], rejected_reasons: list[str]):
        self.accepted = accepted
        self.rejected_reasons = rejected_reasons


def accept_output(raw: str, known_evidence_ids: set[str]) -> AcceptResult:
    """
    Validate and accept node output.

    Returns AcceptResult with:
    - accepted: NodeOutput if valid, None if rejected
    - rejected_reasons: list of rejection reasons

    Rejects if:
    - invalid JSON or schema mismatch
    - consequential claim (EXTERNAL_FACT, OBSERVED_RELATION, INFERENCE) has empty evidence_ids
      or ids not in known_evidence_ids
    - UNKNOWN-typed statement is allowed with no evidence only if coverage for its
      protocol_class is SEARCHED_NONE_FOUND
    """
    if raw is None:
        return AcceptResult(None, ["raw input is None (provider timeout or failure)"])

    rejected_reasons = []

    # Parse JSON
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        return AcceptResult(None, [f"invalid JSON: {str(e)}"])

    # Validate schema
    try:
        output = NodeOutput(**data)
    except ValidationError as e:
        return AcceptResult(None, [f"schema validation error: {str(e)}"])

    # Check consequential claims have evidence
    for claim in output.claims:
        is_consequential = claim.claim_type in {
            ClaimType.EXTERNAL_FACT,
            ClaimType.OBSERVED_RELATION,
            ClaimType.INFERENCE,
        }

        if is_consequential:
            # Consequential claim must have evidence_ids
            if not claim.evidence_ids:
                # Check if this is an UNKNOWN statement with no evidence
                if claim.claim_type.value == "UNKNOWN":
                    # UNKNOWN type is allowed with no evidence only if coverage
                    # for protocol_class is SEARCHED_NONE_FOUND
                    coverage_status = output.coverage.get(claim.protocol_class)
                    if coverage_status != CoverageStatus.SEARCHED_NONE_FOUND:
                        rejected_reasons.append(
                            f"UNKNOWN claim in '{claim.protocol_class}' with no evidence "
                            f"requires SEARCHED_NONE_FOUND coverage, got {coverage_status}"
                        )
                else:
                    rejected_reasons.append(
                        f"{claim.claim_type.value} claim '{claim.statement}' has no evidence"
                    )
            else:
                # All evidence_ids must be known
                unknown_ids = set(claim.evidence_ids) - known_evidence_ids
                if unknown_ids:
                    rejected_reasons.append(
                        f"claim has unknown evidence IDs: {unknown_ids}"
                    )

    if rejected_reasons:
        return AcceptResult(None, rejected_reasons)

    return AcceptResult(output, [])


def apply_output(state, result: AcceptResult):
    """
    Apply result to state.
    Returns the SAME state object unchanged when accepted is None.
    """
    if result.accepted is None:
        return state
    # TODO: implement actual state application when needed
    return state
