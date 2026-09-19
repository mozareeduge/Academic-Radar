import pytest
from academic_radar.research.provider import MockProvider, LiteLLMProvider
from academic_radar.research.run_identity import make_run_identity, assert_no_secrets


class TestMockProvider:
    """Test MockProvider implementation."""

    def test_mock_provider_scripted_output(self):
        """MockProvider returns the scripted response for a given schema."""
        script = {
            "schema_a": "response_a",
            "schema_b": "response_b",
        }
        provider = MockProvider(script)

        result = provider.complete([], schema_name="schema_a")
        assert result == "response_a"

        result = provider.complete([], schema_name="schema_b")
        assert result == "response_b"

    def test_mock_provider_unscripted_schema_raises(self):
        """MockProvider raises KeyError for unscripted schemas."""
        script = {"schema_a": "response_a"}
        provider = MockProvider(script)

        with pytest.raises(KeyError):
            provider.complete([], schema_name="unknown_schema")


class TestRunIdentity:
    """Test run identity creation and validation."""

    def test_identity_has_all_six_fields(self):
        """make_run_identity returns dict with exactly six fields."""
        identity = make_run_identity(
            model_id="openai/gpt-4o-mini",
            provider_id="openai",
            prompt_text="Test prompt",
            schema_version="1.0",
            protocol_version="1.0",
            run_id="run-123",
        )

        assert len(identity) == 6
        assert "model_id" in identity
        assert "provider_id" in identity
        assert "prompt_hash" in identity
        assert "schema_version" in identity
        assert "protocol_version" in identity
        assert "run_id" in identity

    def test_identity_prompt_hash_is_sha256(self):
        """Prompt hash is sha256 of the prompt text."""
        import hashlib
        prompt = "Test prompt content"
        identity = make_run_identity(
            model_id="openai/gpt-4o-mini",
            provider_id="openai",
            prompt_text=prompt,
            schema_version="1.0",
            protocol_version="1.0",
            run_id="run-123",
        )

        expected_hash = hashlib.sha256(prompt.encode()).hexdigest()
        assert identity["prompt_hash"] == expected_hash

    def test_identity_passes_assert_no_secrets(self):
        """Valid identity passes assert_no_secrets without raising."""
        identity = make_run_identity(
            model_id="openai/gpt-4o-mini",
            provider_id="openai",
            prompt_text="Test prompt",
            schema_version="1.0",
            protocol_version="1.0",
            run_id="run-123",
        )

        # Should not raise
        assert_no_secrets(identity)

    def test_identity_with_secret_key_raises(self):
        """Identity containing a secret key fails assert_no_secrets."""
        identity = make_run_identity(
            model_id="sk-test1234567890abcdef",
            provider_id="openai",
            prompt_text="Test prompt",
            schema_version="1.0",
            protocol_version="1.0",
            run_id="run-123",
        )

        with pytest.raises(AssertionError) as exc_info:
            assert_no_secrets(identity)

        assert "secrets" in str(exc_info.value).lower()
