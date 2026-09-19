"""User disposition and suggestion persistence.

ORACLE-002: User disposition is automation-proof. Crawls, model research,
deterministic suggestion recomputation, and evidence refresh cannot mutate
the persisted user disposition.

ORACLE-003: System suggestion is transparent and deterministic.
Reasons/inputs are inspectable.

DEC-004: Only the user persists STRONG/WATCH/ACT/REJECTED. Automations may
suggest but not silently decide.
"""

from sqlalchemy.orm import Session
from db.radar_models_cases import EvaluationCase, CaseDispositionHistory
from academic_radar.domain.suggestions import Suggestion


def set_user_disposition(
    session: Session,
    case_id: str,
    new_value: str,
    *,
    actor: str,
    reason: str = ""
) -> None:
    """Set user disposition on a case with audit history.

    Only USER can set user_disposition. SYSTEM_SUGGESTION cannot.

    Raises PermissionError if actor != 'USER'.

    Args:
        session: SQLAlchemy session
        case_id: The evaluation case ID
        new_value: The new disposition (STRONG, WATCH, ACT, REJECTED, UNDECIDED)
        actor: Who is making this change ('USER' or 'SYSTEM_SUGGESTION')
        reason: Optional reason for the change
    """
    if actor != "USER":
        raise PermissionError(f"Only USER can set user_disposition, got {actor}")

    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    previous = case.user_disposition

    history_entry = CaseDispositionHistory(
        case_id=case_id,
        previous=previous,
        new=new_value,
        actor=actor,
        reason=reason if reason else None
    )
    session.add(history_entry)

    case.user_disposition = new_value
    session.flush()


def save_suggestion(session: Session, case_id: str, suggestion: Suggestion) -> None:
    """Save suggestion to case, updating only suggested_disposition.

    Never touches user_disposition. The suggestion is derived and advisory only.

    Args:
        session: SQLAlchemy session
        case_id: The evaluation case ID
        suggestion: The Suggestion object with value, reasons, uncertainties
    """
    case = session.query(EvaluationCase).filter(EvaluationCase.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    case.suggested_disposition = suggestion.value.value
    session.flush()
