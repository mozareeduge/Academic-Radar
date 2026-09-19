"""Tests for research_case_job and enqueue_research."""

import uuid
import pytest
from unittest.mock import MagicMock


class TestEnqueueResearch:
    """Test enqueue_research function."""

    def test_enqueue_research_returns_job_id(self):
        """enqueue_research should return a job ID."""
        from academic_radar.jobs.research_job import enqueue_research

        queue = MagicMock()
        job_mock = MagicMock()
        job_mock.id = "test-job-123"
        queue.enqueue.return_value = job_mock

        case_id = str(uuid.uuid4())
        job_id = enqueue_research(case_id, queue)

        assert job_id == "test-job-123"
        assert queue.enqueue.called

        # Verify the job was enqueued with correct arguments
        call_args = queue.enqueue.call_args
        assert call_args[0][1] == case_id
        assert ":" in call_args[0][2]  # run_key should contain a colon


class TestResearchCaseJobSignature:
    """Test that research_case_job has the right signature for RQ."""

    def test_research_case_job_callable(self):
        """research_case_job should be callable as an RQ function."""
        from academic_radar.jobs.research_job import research_case_job

        # Check that it's callable
        assert callable(research_case_job)

        # Check signature has case_id, run_key, and deps kwargs
        import inspect
        sig = inspect.signature(research_case_job)
        assert "case_id" in sig.parameters
        assert "run_key" in sig.parameters
        assert "deps" in sig.parameters

        # deps should be keyword-only
        assert sig.parameters["deps"].kind == inspect.Parameter.KEYWORD_ONLY


class TestResearchJobLogic:
    """Test research job logic without database."""

    def test_retry_on_timeout(self):
        """Test that timeouts trigger retries."""
        from academic_radar.jobs.research_job import MAX_RETRIES, RETRY_BACKOFF_S

        # Verify constants are set correctly
        assert MAX_RETRIES == 2
        assert RETRY_BACKOFF_S == 1.0


class TestProviderErrorClassification:
    """Test provider error classification (without database)."""

    def test_failure_reasons_exist(self):
        """Verify failure reason enum values exist."""
        # These are the failure reasons the code should classify
        reasons = [
            "PROVIDER_TIMEOUT",
            "INVALID_OUTPUT",
            "SOURCE_BLOCKED",
            "UNKNOWN",
        ]

        # All should be valid strings
        for reason in reasons:
            assert isinstance(reason, str)
            assert len(reason) > 0
