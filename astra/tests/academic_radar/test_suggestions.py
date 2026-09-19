"""Test suggestions, freshness, and disposition logic.

QA-P02: Disposition immutability under automation
Set WATCH; run new evidence ingestion and suggestion recomputation. Verify
user disposition remains WATCH while system suggestion may change with
traceable inputs.
Negative canary: intentionally route suggestion save into user disposition;
test must fail.
"""

import pytest
from datetime import datetime, timezone, timedelta

from academic_radar.domain.suggestions import Suggestion, suggest
from academic_radar.domain.enums import UserDisposition, GateResult
from academic_radar.domain.gates import Gate
from academic_radar.domain.freshness import is_stale
from academic_radar.domain.protocols import Protocol
from academic_radar.domain.disposition import set_user_disposition, save_suggestion
from db.radar_models_cases import EvaluationCase
from tests.academic_radar.canary import expect_violation


class TestSuggestBasics:
    """Test basic suggestion derivation logic."""

    def test_suggest_no_facts_undecided(self):
        """Empty case facts => UNDECIDED suggestion."""
        suggestion = suggest({})
        assert suggestion.value == UserDisposition.UNDECIDED
        assert suggestion.reasons == []
        assert suggestion.uncertainties == []

    def test_suggest_hard_blocker_rejected(self):
        """Hard blocker (FAIL gate) => REJECTED suggestion."""
        blocker = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.FAIL,
            evidence_ids=["ev1"]
        )
        suggestion = suggest({"hard_blockers": [blocker]})
        assert suggestion.value == UserDisposition.REJECTED
        assert "formal blocker" in suggestion.reasons

    def test_suggest_unknown_hard_gate_watch(self):
        """Unknown hard gate => WATCH suggestion."""
        unknown_gate = Gate(
            name="second_ma_rule",
            hard=True,
            result=GateResult.UNKNOWN,
            evidence_ids=[]
        )
        suggestion = suggest({"unknown_hard_gates": [unknown_gate]})
        assert suggestion.value == UserDisposition.WATCH
        assert "eligibility uncertain" in suggestion.reasons

    def test_suggest_critical_deadline_act(self):
        """Critical deadline (≤7d) and no blockers => ACT."""
        suggestion = suggest({"deadline_urgency": "critical"})
        assert suggestion.value == UserDisposition.ACT
        assert any("deadline ≤7" in r for r in suggestion.reasons)

    def test_suggest_high_deadline_watch(self):
        """High deadline (≤30d) and no blockers => WATCH."""
        suggestion = suggest({"deadline_urgency": "high"})
        assert suggestion.value == UserDisposition.WATCH
        assert any("deadline ≤30" in r for r in suggestion.reasons)

    def test_suggest_stale_critical_watch(self):
        """Stale critical facts => WATCH."""
        suggestion = suggest({"stale_critical_facts": ["supervisor_track"]})
        assert suggestion.value == UserDisposition.WATCH
        assert any("stale critical fact" in r for r in suggestion.reasons)

    def test_suggest_dimension_unknowns_uncertainty(self):
        """Dimension unknowns => added to uncertainties."""
        suggestion = suggest({"dimension_unknowns": ["supervision_track", "research_fit"]})
        assert len(suggestion.uncertainties) >= 2
        assert any("dimension unknown" in u for u in suggestion.uncertainties)


class TestSuggestNoProbalityWords:
    """Test that suggestions never use probability language.

    DEC-030: Do not use probability labels without real base-rate evidence.
    Prefer formally strong, intellectually strong, funding weak, eligibility
    uncertain, etc.
    """

    def test_no_probability_words_in_reasons(self):
        """Reason strings never contain probability words."""
        probability_words = ["chance", "likely", "probably", "possibly", "may", "might", "could"]

        suggestion = suggest({"deadline_urgency": "critical", "stale_critical_facts": ["test"]})

        for reason in suggestion.reasons:
            for prob_word in probability_words:
                assert prob_word.lower() not in reason.lower(), \
                    f"Probability word '{prob_word}' found in reason: {reason}"

    def test_no_probability_words_in_uncertainties(self):
        """Uncertainty strings never contain probability words."""
        probability_words = ["chance", "likely", "probably", "possibly", "may", "might", "could"]

        suggestion = suggest({"dimension_unknowns": ["unknown_dim"]})

        for uncertainty in suggestion.uncertainties:
            for prob_word in probability_words:
                assert prob_word.lower() not in uncertainty.lower(), \
                    f"Probability word '{prob_word}' found in uncertainty: {uncertainty}"


class TestDispositionUserOnly:
    """Test that only USER can set user_disposition.

    ORACLE-002: User disposition is automation-proof.
    """

    def test_set_user_disposition_permission_check(self):
        """Only USER actor can call set_user_disposition."""
        # Mock session and case for testing permission check
        from unittest.mock import Mock, MagicMock

        mock_session = Mock()
        mock_case = Mock(spec=EvaluationCase)
        mock_case.id = "case123"
        mock_case.user_disposition = "UNDECIDED"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_case

        # USER should succeed (we can't check full behavior without real DB, but at least check it doesn't raise)
        set_user_disposition(mock_session, "case123", "WATCH", actor="USER", reason="testing")
        assert True

    def test_set_user_disposition_by_system_raises(self):
        """Non-USER actor raises PermissionError."""
        from unittest.mock import Mock

        mock_session = Mock()

        with pytest.raises(PermissionError, match="Only USER"):
            set_user_disposition(mock_session, "case123", "WATCH", actor="SYSTEM_SUGGESTION")


class TestSaveSuggestionImmutable:
    """Test that save_suggestion updates only suggested_disposition.

    ORACLE-002: User disposition is automation-proof. Crawls, model research,
    and suggestion recomputation cannot mutate user_disposition.
    """

    def test_save_suggestion_updates_suggested_only(self):
        """save_suggestion updates suggested_disposition, never user_disposition."""
        from unittest.mock import Mock

        mock_session = Mock()
        mock_case = Mock(spec=EvaluationCase)
        mock_case.id = "case123"
        mock_case.user_disposition = "WATCH"
        mock_case.suggested_disposition = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_case

        suggestion = Suggestion(
            value=UserDisposition.ACT,
            reasons=["test"],
            uncertainties=[]
        )
        save_suggestion(mock_session, "case123", suggestion)

        # Verify only suggested_disposition was set
        assert mock_case.suggested_disposition == "ACT"
        assert mock_case.user_disposition == "WATCH", "user_disposition must not be touched"

    def test_save_suggestion_different_values(self):
        """save_suggestion does not change user_disposition regardless of suggestion."""
        from unittest.mock import Mock

        mock_session = Mock()
        mock_case = Mock(spec=EvaluationCase)
        mock_case.id = "case123"
        mock_case.user_disposition = "WATCH"
        mock_case.suggested_disposition = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_case

        suggestion = Suggestion(
            value=UserDisposition.REJECTED,
            reasons=["blocker found"],
            uncertainties=[]
        )
        save_suggestion(mock_session, "case123", suggestion)

        assert mock_case.suggested_disposition == "REJECTED"
        assert mock_case.user_disposition == "WATCH", "user_disposition must remain WATCH"


class TestFreshness:
    """Test freshness computation.

    DEC-028: Each consequential external fact exposes last checked.
    """

    def test_is_stale_within_freshness_window(self):
        """Evidence within freshness window is not stale."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_track",),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_track": 30}
        )

        now = datetime.now(timezone.utc)
        last_checked = now - timedelta(days=15)

        is_stale_result = is_stale(last_checked, "supervisor_track", protocol, now)
        assert is_stale_result is False

    def test_is_stale_beyond_freshness_window(self):
        """Evidence beyond freshness window is stale."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_track",),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={"supervisor_track": 30}
        )

        now = datetime.now(timezone.utc)
        last_checked = now - timedelta(days=45)

        is_stale_result = is_stale(last_checked, "supervisor_track", protocol, now)
        assert is_stale_result is True

    def test_is_stale_no_rule_not_stale(self):
        """Evidence class with no freshness rule is never stale."""
        protocol = Protocol(
            application_route="MA_PROGRAMME",
            version="1.0",
            mandatory=("supervisor_track",),
            optional=(),
            allow_zero_result=False,
            allowed_unknowns=(),
            blocking_unknowns=(),
            freshness_days={}
        )

        now = datetime.now(timezone.utc)
        last_checked = now - timedelta(days=1000)

        is_stale_result = is_stale(last_checked, "supervisor_track", protocol, now)
        assert is_stale_result is False


@pytest.mark.canary
def test_canary_user_disposition_overwrite():
    """Canary: detect if save_suggestion accidentally writes user_disposition.

    This test uses a mutated save_suggestion that incorrectly writes user_disposition.
    The assertion checking user_disposition must be detected by expect_violation.
    """
    from unittest.mock import Mock

    mock_session = Mock()
    mock_case = Mock(spec=EvaluationCase)
    mock_case.id = "case123"
    mock_case.user_disposition = "WATCH"
    mock_case.suggested_disposition = None
    mock_session.query.return_value.filter.return_value.first.return_value = mock_case

    suggestion = Suggestion(
        value=UserDisposition.REJECTED,
        reasons=["blocker"],
        uncertainties=[]
    )

    def mutated_save_suggestion(session, cid, sugg):
        case_obj = session.query(EvaluationCase).filter(EvaluationCase.id == cid).first()
        if not case_obj:
            raise ValueError(f"Case {cid} not found")
        case_obj.suggested_disposition = sugg.value.value
        case_obj.user_disposition = sugg.value.value  # BUG: should not do this
        session.flush()

    mutated_save_suggestion(mock_session, "case123", suggestion)

    def check_immutability():
        assert mock_case.user_disposition == "WATCH", "user_disposition must remain WATCH"

    expect_violation(check_immutability)
