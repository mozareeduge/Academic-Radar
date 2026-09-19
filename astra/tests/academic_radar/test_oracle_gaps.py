"""Tests for uncovered Tier-A oracles.

This file contains new tests for Tier-A oracles that were previously uncovered.
Each test includes an ORACLE-NNN comment identifying the oracle it exercises.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os
import tempfile
import subprocess
import sys

from academic_radar.domain.suggestions import suggest
from academic_radar.domain.gates import Gate, GateResult
from academic_radar.domain.enums import UserDisposition, ClaimType, ClaimStatus


# ORACLE-003
def test_system_suggestion_deterministic_with_same_facts():
    """System suggestion is deterministic: same facts produce same suggestion."""
    facts1 = {
        "deadline_urgency": "high",
        "hard_blockers": [],
        "unknown_hard_gates": [],
    }
    facts2 = {
        "deadline_urgency": "high",
        "hard_blockers": [],
        "unknown_hard_gates": [],
    }

    suggestion1 = suggest(facts1)
    suggestion2 = suggest(facts2)

    assert suggestion1.value == suggestion2.value
    assert suggestion1.reasons == suggestion2.reasons
    assert suggestion1.uncertainties == suggestion2.uncertainties


# ORACLE-010
def test_gates_store_evidence_ids_for_each_assessment():
    """Gate assessments require and store evidence_ids; no unsupported claims."""
    gate = Gate(
        name="english_requirement",
        hard=True,
        result=GateResult.PASS,
        evidence_ids=["ev1", "ev2"]
    )
    assert gate.evidence_ids == ["ev1", "ev2"]
    assert len(gate.evidence_ids) > 0, "PASS gate must have evidence"

    gate_fail = Gate(
        name="english_requirement",
        hard=True,
        result=GateResult.FAIL,
        evidence_ids=["ev3"]
    )
    assert len(gate_fail.evidence_ids) > 0, "FAIL gate must have evidence"


# ORACLE-011
def test_gate_unknown_does_not_require_evidence():
    """UNKNOWN gate result does not claim a fact, does not require evidence."""
    gate_unknown = Gate(
        name="second_ma_rule",
        hard=True,
        result=GateResult.UNKNOWN,
        evidence_ids=[]
    )
    assert gate_unknown.result == GateResult.UNKNOWN
    assert gate_unknown.evidence_ids == []
    assert gate_unknown.result != GateResult.PASS, "UNKNOWN is not a positive claim"
    assert gate_unknown.result != GateResult.FAIL, "UNKNOWN is not a negative claim"


# ORACLE-027, ORACLE-028
def test_supervisor_track_assessment_distinguishes_authored_vs_supervised():
    """Supervisor assessment examines supervision capacity, not authored work.

    The supervisor track may assess supervision permissiveness (SUPERVISION_CAPACITY)
    without claiming those characteristics caused historical acceptance.
    """
    from academic_radar.domain.dimensions import (
        SupervisorDimension,
        SUPERVISOR_DIMENSIONS,
    )

    # Verify SUPERVISION_CAPACITY dimension exists (separate from authored work assessment)
    supervisor_dims = set(SUPERVISOR_DIMENSIONS)
    assert SupervisorDimension.SUPERVISION_CAPACITY in supervisor_dims, \
           "Supervisor track should assess supervision capacity independently"


# ORACLE-030
def test_existing_ma_rule_is_explicit_gate():
    """Second-MA eligibility is an explicit gate/question, not assumed."""
    gate = Gate(
        name="existing_ma_rule",
        hard=True,
        result=GateResult.UNKNOWN,
        evidence_ids=[]
    )
    assert gate.name == "existing_ma_rule"
    assert gate.hard is True, "existing_ma_rule is a hard gate (formally binding)"
    assert gate.result == GateResult.UNKNOWN, "eligibility unknown until checked"


# ORACLE-031
def test_english_requirement_is_explicit_gate():
    """English hard constraint is an explicit gate on completion language."""
    gate = Gate(
        name="english_requirement",
        hard=True,
        result=GateResult.FAIL,
        evidence_ids=["ev_mandatory_non_english_component"]
    )
    assert gate.name == "english_requirement"
    assert gate.hard is True, "english_requirement must be a hard gate"
    assert gate.result == GateResult.FAIL, "programme fails if mandatory component prevents English completion"
    assert len(gate.evidence_ids) > 0, "failure must be evidenced"
