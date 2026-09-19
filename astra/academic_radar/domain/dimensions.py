from enum import Enum
from typing import Optional


class SupervisorDimension(str, Enum):
    TOPIC_RESONANCE = "TOPIC_RESONANCE"
    METHOD_ALIGNMENT = "METHOD_ALIGNMENT"
    THEORY_ALIGNMENT = "THEORY_ALIGNMENT"
    TRACK_B_PRACTICE_OPENNESS = "TRACK_B_PRACTICE_OPENNESS"
    ECOSYSTEM_INFRASTRUCTURE = "ECOSYSTEM_INFRASTRUCTURE"
    SUPERVISION_CAPACITY = "SUPERVISION_CAPACITY"
    FUNDING_PLAUSIBILITY = "FUNDING_PLAUSIBILITY"


SUPERVISOR_DIMENSIONS = (
    SupervisorDimension.TOPIC_RESONANCE,
    SupervisorDimension.METHOD_ALIGNMENT,
    SupervisorDimension.THEORY_ALIGNMENT,
    SupervisorDimension.TRACK_B_PRACTICE_OPENNESS,
    SupervisorDimension.ECOSYSTEM_INFRASTRUCTURE,
    SupervisorDimension.SUPERVISION_CAPACITY,
    SupervisorDimension.FUNDING_PLAUSIBILITY,
)


class MAHead(str, Enum):
    ADMISSION_VIABILITY = "ADMISSION_VIABILITY"
    FUNDING_VIABILITY = "FUNDING_VIABILITY"
    STRATEGIC_VALUE = "STRATEGIC_VALUE"


MA_HEADS = (
    MAHead.ADMISSION_VIABILITY,
    MAHead.FUNDING_VIABILITY,
    MAHead.STRATEGIC_VALUE,
)


class MAHeadValue(str, Enum):
    STRONG = "STRONG"
    MIXED = "MIXED"
    WEAK = "WEAK"
    UNKNOWN = "UNKNOWN"


def assess_dimension(
    dim: SupervisorDimension,
    value: Optional[int],
    evidence_ids: list[str],
    unknowns: list[str],
) -> dict:
    """
    Assess a supervisor dimension.

    Args:
        dim: The dimension being assessed
        value: 0-3 integer or None (None means Unknown)
        evidence_ids: List of evidence artifact IDs supporting the value
        unknowns: List of unknown evidence gaps

    Returns:
        Dict with dimension, value, evidence_ids, unknowns

    Raises:
        ValueError: if value is not None/0-3, or if value is not None but evidence_ids is empty
    """
    if value is not None:
        if not isinstance(value, int) or value < 0 or value > 3:
            raise ValueError(f"value must be None or int 0-3, got {value}")
        if not evidence_ids:
            raise ValueError(f"non-None value requires evidence_ids")

    return {
        "dimension": dim,
        "value": value,
        "evidence_ids": evidence_ids,
        "unknowns": unknowns,
    }


def summarize_supervisor(assessments: list[dict]) -> dict:
    """
    Summarize supervisor dimension assessments.

    Args:
        assessments: List of assessment dicts from assess_dimension()

    Returns:
        Dict with all seven dimension values (int/None) and unknown_dims list.
        No total, average, overall, or score key.
    """
    result = {}
    unknown_dims = []

    for assessment in assessments:
        dim = assessment["dimension"]
        value = assessment["value"]
        result[dim] = value
        if value is None:
            unknown_dims.append(dim)

    result["unknown_dims"] = unknown_dims
    return result


def summarize_ma(heads: list[dict]) -> dict:
    """
    Summarize MA assessment heads.

    Args:
        heads: List of head assessment dicts with keys: head, value, evidence_ids, unknowns

    Returns:
        Dict with each head's value (STRONG/MIXED/WEAK/UNKNOWN) plus evidence_ids and unknowns lists.
        No combined field.
    """
    result = {}
    all_evidence_ids = []
    all_unknowns = []

    for head in heads:
        head_key = head["head"]
        value = head["value"]
        result[head_key] = value
        all_evidence_ids.extend(head.get("evidence_ids", []))
        all_unknowns.extend(head.get("unknowns", []))

    result["evidence_ids"] = all_evidence_ids
    result["unknowns"] = all_unknowns
    return result
