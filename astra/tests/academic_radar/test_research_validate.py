import pytest
import json
from academic_radar.research.validate import accept_output, apply_output, AcceptResult
from academic_radar.research.schemas.nodes import ClaimOut, NodeOutput
from academic_radar.domain.enums import ClaimType, CoverageStatus
from tests.academic_radar.canary import expect_violation


class TestAcceptOutputValidClaim:
    def test_valid_claim_with_known_ids_accepted(self):
        claim = ClaimOut(
            statement="Supervisor has published in AI",
            claim_type=ClaimType.EXTERNAL_FACT,
            evidence_ids=["ev-001"],
            protocol_class="supervision_recent_work",
        )
        output = NodeOutput(
            schema_version="1.0",
            node="resolve_supervisor_identity",
            claims=[claim],
            coverage={"supervision_recent_work": CoverageStatus.SEARCHED_FOUND},
        )
        known_ids = {"ev-001", "ev-002"}

        raw = output.model_dump_json()
        result = accept_output(raw, known_ids)

        assert result.accepted is not None
        assert result.rejected_reasons == []
        assert result.accepted.claims[0].statement == "Supervisor has published in AI"


class TestAcceptOutputFluentClaimNoEvidence:
    def test_fluent_claim_with_no_evidence_rejected(self):
        claim = ClaimOut(
            statement="This is a consequential inference",
            claim_type=ClaimType.INFERENCE,
            evidence_ids=[],
            protocol_class="some_protocol",
        )
        output = NodeOutput(
            schema_version="1.0",
            node="test_node",
            claims=[claim],
            coverage={"some_protocol": CoverageStatus.SEARCHED_FOUND},
        )
        known_ids = {"ev-001"}

        raw = output.model_dump_json()
        result = accept_output(raw, known_ids)

        assert result.accepted is None
        assert len(result.rejected_reasons) > 0
        assert "no evidence" in result.rejected_reasons[0].lower()


class TestAcceptOutputMalformedJson:
    def test_malformed_json_rejected(self):
        raw = "{ invalid json"
        known_ids = {"ev-001"}

        result = accept_output(raw, known_ids)

        assert result.accepted is None
        assert len(result.rejected_reasons) > 0
        assert "invalid json" in result.rejected_reasons[0].lower()


class TestAcceptOutputProviderTimeout:
    def test_provider_timeout_modelled_as_raw_none_rejected(self):
        raw = None
        known_ids = {"ev-001"}

        result = accept_output(raw, known_ids)

        assert result.accepted is None
        assert len(result.rejected_reasons) > 0


class TestApplyOutputPreservesState:
    def test_apply_output_leaves_prior_state_unchanged_when_accepted_none(self):
        prior_state = {"case_id": "case-123", "status": "REVIEWED"}

        # Create a rejected result
        result = AcceptResult(None, ["some rejection reason"])

        returned_state = apply_output(prior_state, result)

        assert returned_state is prior_state
        assert returned_state == {"case_id": "case-123", "status": "REVIEWED"}


class TestCanaryUnsupportedModelClaim:
    @pytest.mark.canary
    def test_canary_unsupported_model_claim(self):
        """
        Canary to prove that accept_output rejects claims without evidence.
        This tests that a mutated (broken) version that accepts all claims
        would be caught by the canary assertion.
        """
        # This claim has no evidence - should be rejected by correct implementation
        claim = ClaimOut(
            statement="Unsupported claim",
            claim_type=ClaimType.EXTERNAL_FACT,
            evidence_ids=[],
            protocol_class="some_class",
        )
        output = NodeOutput(
            schema_version="1.0",
            node="test",
            claims=[claim],
            coverage={},
        )
        raw = output.model_dump_json()

        # Define a broken version that would incorrectly accept claims without evidence
        def would_accept_unsupported():
            result = accept_output(raw, set())
            # This should fail because we correctly reject
            assert result.accepted is not None, "Broken: should accept"

        # expect_violation will catch the AssertionError raised by the broken check
        expect_violation(would_accept_unsupported)
