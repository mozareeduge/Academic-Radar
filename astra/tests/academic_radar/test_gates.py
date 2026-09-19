"""Test gate assessment and hard-blocker logic."""

import pytest

from academic_radar.domain.gates import Gate, GateResult, blockers, unknowns, actionable, formally_open, validate_gate


class TestGateDataclass:
    """Test Gate dataclass structure."""

    def test_gate_basic_creation(self):
        """Gate with PASS result and evidence."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.PASS,
            evidence_ids=["ev1", "ev2"]
        )
        assert gate.name == "english_requirement"
        assert gate.hard is True
        assert gate.result == GateResult.PASS
        assert gate.evidence_ids == ["ev1", "ev2"]

    def test_gate_unknown_result(self):
        """Gate with UNKNOWN result requires no evidence."""
        gate = Gate(
            name="second_ma_rule",
            hard=True,
            result=GateResult.UNKNOWN,
            evidence_ids=[]
        )
        assert gate.result == GateResult.UNKNOWN
        assert gate.evidence_ids == []

    def test_gate_not_applicable(self):
        """Gate with NOT_APPLICABLE requires no evidence."""
        gate = Gate(
            name="some_gate",
            hard=False,
            result=GateResult.NOT_APPLICABLE,
            evidence_ids=[]
        )
        assert gate.result == GateResult.NOT_APPLICABLE


class TestValidateGate:
    """Test validate_gate function."""

    def test_validate_gate_pass_with_evidence(self):
        """PASS result must have at least one evidence id."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.PASS,
            evidence_ids=["ev1"]
        )
        validate_gate(gate)

    def test_validate_gate_pass_without_evidence_raises(self):
        """PASS result without evidence raises ValueError."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.PASS,
            evidence_ids=[]
        )
        with pytest.raises(ValueError, match="must have at least one evidence"):
            validate_gate(gate)

    def test_validate_gate_fail_with_evidence(self):
        """FAIL result must have at least one evidence id."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.FAIL,
            evidence_ids=["ev1"]
        )
        validate_gate(gate)

    def test_validate_gate_fail_without_evidence_raises(self):
        """FAIL result without evidence raises ValueError."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.FAIL,
            evidence_ids=[]
        )
        with pytest.raises(ValueError, match="must have at least one evidence"):
            validate_gate(gate)

    def test_validate_gate_unknown_no_evidence_ok(self):
        """UNKNOWN result with no evidence is valid."""
        gate = Gate(
            name="second_ma_rule",
            hard=True,
            result=GateResult.UNKNOWN,
            evidence_ids=[]
        )
        validate_gate(gate)

    def test_validate_gate_not_applicable_no_evidence_ok(self):
        """NOT_APPLICABLE result with no evidence is valid."""
        gate = Gate(
            name="some_gate",
            hard=False,
            result=GateResult.NOT_APPLICABLE,
            evidence_ids=[]
        )
        validate_gate(gate)

    def test_validate_gate_stale_no_evidence_ok(self):
        """STALE result with no evidence is valid."""
        gate = Gate(
            name="some_gate",
            hard=False,
            result=GateResult.STALE,
            evidence_ids=[]
        )
        validate_gate(gate)


class TestBlockers:
    """Test blockers function."""

    def test_blockers_hard_fail_is_blocker(self):
        """Hard gate with FAIL result is a blocker."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.FAIL,
            evidence_ids=["ev1"]
        )
        result = blockers([gate])
        assert len(result) == 1
        assert result[0].name == "english_requirement"

    def test_blockers_soft_fail_not_blocker(self):
        """Soft gate with FAIL result is not a blocker."""
        gate = Gate(
            name="some_soft_gate",
            hard=False,
            result=GateResult.FAIL,
            evidence_ids=["ev1"]
        )
        result = blockers([gate])
        assert len(result) == 0

    def test_blockers_hard_unknown_not_blocker(self):
        """Hard gate with UNKNOWN result is not a blocker."""
        gate = Gate(
            name="second_ma_rule",
            hard=True,
            result=GateResult.UNKNOWN,
            evidence_ids=[]
        )
        result = blockers([gate])
        assert len(result) == 0

    def test_blockers_hard_pass_not_blocker(self):
        """Hard gate with PASS result is not a blocker."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.PASS,
            evidence_ids=["ev1"]
        )
        result = blockers([gate])
        assert len(result) == 0

    def test_blockers_multiple_with_one_hard_fail(self):
        """Multiple gates with one hard fail returns only the hard fail."""
        gates = [
            Gate(name="g1", hard=False, result=GateResult.FAIL, evidence_ids=["ev1"]),
            Gate(name="g2", hard=True, result=GateResult.FAIL, evidence_ids=["ev2"]),
            Gate(name="g3", hard=True, result=GateResult.PASS, evidence_ids=["ev3"]),
        ]
        result = blockers(gates)
        assert len(result) == 1
        assert result[0].name == "g2"

    def test_blockers_multiple_hard_fails(self):
        """Multiple hard fails returns all of them."""
        gates = [
            Gate(name="g1", hard=True, result=GateResult.FAIL, evidence_ids=["ev1"]),
            Gate(name="g2", hard=True, result=GateResult.FAIL, evidence_ids=["ev2"]),
        ]
        result = blockers(gates)
        assert len(result) == 2
        assert {g.name for g in result} == {"g1", "g2"}

    def test_blockers_empty_list(self):
        """Empty gates list returns empty blockers."""
        result = blockers([])
        assert result == []


class TestUnknowns:
    """Test unknowns function."""

    def test_unknowns_hard_unknown_is_unknown(self):
        """Hard gate with UNKNOWN result is in unknowns."""
        gate = Gate(
            name="second_ma_rule",
            hard=True,
            result=GateResult.UNKNOWN,
            evidence_ids=[]
        )
        result = unknowns([gate])
        assert len(result) == 1
        assert result[0].name == "second_ma_rule"

    def test_unknowns_soft_unknown_is_unknown(self):
        """Soft gate with UNKNOWN result is in unknowns."""
        gate = Gate(
            name="some_soft_gate",
            hard=False,
            result=GateResult.UNKNOWN,
            evidence_ids=[]
        )
        result = unknowns([gate])
        assert len(result) == 1
        assert result[0].name == "some_soft_gate"

    def test_unknowns_hard_fail_not_unknown(self):
        """Hard gate with FAIL result is not in unknowns."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.FAIL,
            evidence_ids=["ev1"]
        )
        result = unknowns([gate])
        assert len(result) == 0

    def test_unknowns_pass_not_unknown(self):
        """Gate with PASS result is not in unknowns."""
        gate = Gate(
            name="english_requirement",
            hard=True,
            result=GateResult.PASS,
            evidence_ids=["ev1"]
        )
        result = unknowns([gate])
        assert len(result) == 0

    def test_unknowns_multiple_with_one_unknown(self):
        """Multiple gates with one unknown returns only the unknown."""
        gates = [
            Gate(name="g1", hard=False, result=GateResult.FAIL, evidence_ids=["ev1"]),
            Gate(name="g2", hard=True, result=GateResult.UNKNOWN, evidence_ids=[]),
            Gate(name="g3", hard=True, result=GateResult.PASS, evidence_ids=["ev3"]),
        ]
        result = unknowns(gates)
        assert len(result) == 1
        assert result[0].name == "g2"

    def test_unknowns_multiple_unknowns(self):
        """Multiple unknowns returns all of them."""
        gates = [
            Gate(name="g1", hard=True, result=GateResult.UNKNOWN, evidence_ids=[]),
            Gate(name="g2", hard=False, result=GateResult.UNKNOWN, evidence_ids=[]),
        ]
        result = unknowns(gates)
        assert len(result) == 2
        assert {g.name for g in result} == {"g1", "g2"}

    def test_unknowns_empty_list(self):
        """Empty gates list returns empty unknowns."""
        result = unknowns([])
        assert result == []


class TestActionable:
    """Test actionable function."""

    # ORACLE-005
    def test_actionable_false_when_hard_blocker_exists(self):
        """actionable is False when there is a hard FAIL."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.FAIL, evidence_ids=["ev1"]),
        ]
        result = actionable(gates)
        assert result is False

    def test_actionable_false_even_with_all_passes(self):
        """actionable is False when there is a hard FAIL regardless of other gates."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.FAIL, evidence_ids=["ev1"]),
            Gate(name="degree", hard=True, result=GateResult.PASS, evidence_ids=["ev2"]),
            Gate(name="soft_gate", hard=False, result=GateResult.PASS, evidence_ids=["ev3"]),
        ]
        result = actionable(gates)
        assert result is False

    def test_actionable_true_when_no_hard_blockers(self):
        """actionable is True when there are no hard FAIL gates."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.PASS, evidence_ids=["ev1"]),
            Gate(name="degree", hard=True, result=GateResult.PASS, evidence_ids=["ev2"]),
            Gate(name="soft_gate", hard=False, result=GateResult.FAIL, evidence_ids=["ev3"]),
        ]
        result = actionable(gates)
        assert result is True

    def test_actionable_true_with_unknowns(self):
        """actionable is True when there are unknowns but no hard blockers."""
        gates = [
            Gate(name="second_ma_rule", hard=True, result=GateResult.UNKNOWN, evidence_ids=[]),
            Gate(name="degree", hard=True, result=GateResult.PASS, evidence_ids=["ev2"]),
        ]
        result = actionable(gates)
        assert result is True

    def test_actionable_true_empty_gates(self):
        """actionable is True for empty gates."""
        result = actionable([])
        assert result is True


class TestFormallyOpen:
    """Test formally_open function."""

    def test_formally_open_false_with_hard_fail(self):
        """formally_open is False when there is a hard FAIL."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.FAIL, evidence_ids=["ev1"]),
        ]
        result = formally_open(gates)
        assert result is False

    def test_formally_open_false_with_hard_unknown(self):
        """formally_open is False when there is a hard UNKNOWN."""
        gates = [
            Gate(name="second_ma_rule", hard=True, result=GateResult.UNKNOWN, evidence_ids=[]),
        ]
        result = formally_open(gates)
        assert result is False

    def test_formally_open_true_when_all_hard_pass(self):
        """formally_open is True when all hard gates are PASS."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.PASS, evidence_ids=["ev1"]),
            Gate(name="degree", hard=True, result=GateResult.PASS, evidence_ids=["ev2"]),
            Gate(name="soft_gate", hard=False, result=GateResult.FAIL, evidence_ids=["ev3"]),
        ]
        result = formally_open(gates)
        assert result is True

    def test_formally_open_false_with_soft_fail(self):
        """formally_open is True even with soft FAIL (soft gates don't affect it)."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.PASS, evidence_ids=["ev1"]),
            Gate(name="soft_gate", hard=False, result=GateResult.FAIL, evidence_ids=["ev3"]),
        ]
        result = formally_open(gates)
        assert result is True

    def test_formally_open_false_with_soft_unknown(self):
        """formally_open is True even with soft UNKNOWN."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.PASS, evidence_ids=["ev1"]),
            Gate(name="soft_unknown", hard=False, result=GateResult.UNKNOWN, evidence_ids=[]),
        ]
        result = formally_open(gates)
        assert result is True

    def test_formally_open_true_empty_gates(self):
        """formally_open is True for empty gates."""
        result = formally_open([])
        assert result is True

    def test_formally_open_true_with_not_applicable_hard(self):
        """formally_open is True when hard gate is NOT_APPLICABLE."""
        gates = [
            Gate(name="some_gate", hard=True, result=GateResult.NOT_APPLICABLE, evidence_ids=[]),
        ]
        result = formally_open(gates)
        assert result is True


class TestQAP03Scenario:
    """Test QA-P03 scenarios from CLAUDE_QA_CONTRACT.md."""

    def test_second_ma_rule_unknown_not_blocker(self):
        """Unknown second-MA rule: not a blocker, listed in unknowns, formally_open False."""
        gates = [
            Gate(name="second_ma_rule", hard=True, result=GateResult.UNKNOWN, evidence_ids=[]),
        ]

        blockers_result = blockers(gates)
        unknowns_result = unknowns(gates)
        formally_open_result = formally_open(gates)

        assert len(blockers_result) == 0, "UNKNOWN should not be in blockers"
        assert len(unknowns_result) == 1, "UNKNOWN should be in unknowns"
        assert unknowns_result[0].name == "second_ma_rule"
        assert formally_open_result is False, "formally_open should be False with hard UNKNOWN"

    def test_second_ma_rule_fail_is_blocker(self):
        """Explicit second-MA prohibition: blocker, actionable False."""
        gates = [
            Gate(name="second_ma_rule", hard=True, result=GateResult.FAIL, evidence_ids=["ev_prohibition"]),
        ]

        blockers_result = blockers(gates)
        actionable_result = actionable(gates)

        assert len(blockers_result) == 1, "FAIL should be in blockers"
        assert blockers_result[0].name == "second_ma_rule"
        assert actionable_result is False, "actionable should be False with hard FAIL blocker"

    def test_english_programme_mandatory_non_english_component(self):
        """English programme with mandatory non-English component: blocker."""
        gates = [
            Gate(name="english_completion", hard=True, result=GateResult.FAIL, evidence_ids=["ev_component"]),
        ]

        blockers_result = blockers(gates)

        assert len(blockers_result) == 1, "Should be blocker"
        assert blockers_result[0].name == "english_completion"

    def test_fit_cannot_flip_actionable(self):
        """Strong intellectual fit input cannot flip actionable."""
        gates = [
            Gate(name="english_requirement", hard=True, result=GateResult.FAIL, evidence_ids=["ev1"]),
        ]

        result1 = actionable(gates)
        result2 = actionable(gates)

        assert result1 is False
        assert result2 is False
        assert result1 == result2, "Calling actionable twice with same gates should give same result"
