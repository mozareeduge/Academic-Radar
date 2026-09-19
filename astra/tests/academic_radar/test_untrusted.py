import json
import pytest
from academic_radar.security.untrusted import wrap_untrusted, build_messages
from academic_radar.security.injection import detect_injection
from academic_radar.security.redact import redact
from academic_radar.security.actions import ActionAdapter, run_pipeline_over_source
from tests.academic_radar.canary import expect_violation


@pytest.fixture
def injection_fixtures():
    fixture_path = "tests/academic_radar/fixtures/injection_sources.json"
    with open(fixture_path) as f:
        return json.load(f)


# ORACLE-012
def test_wrap_untrusted_neutralizes_closing_tag(injection_fixtures):
    source = injection_fixtures[0]
    wrapped = wrap_untrusted(source["id"], source["text"])
    assert wrapped.startswith(f"<UNTRUSTED_SOURCE id={source['id']}>")
    assert wrapped.endswith("</UNTRUSTED_SOURCE>")
    assert "</UNTRUSTED_SOURCE>" not in source["text"] or "[NEUTRALIZED_CLOSING_TAG]" in wrapped


def test_detect_injection_finds_hostile_patterns(injection_fixtures):
    for source in injection_fixtures:
        labels = detect_injection(source["text"])
        assert len(labels) > 0, f"Expected labels for {source['id']}, got none"


# ORACLE-012, ORACLE-033
def test_run_pipeline_leaves_adapter_calls_empty(injection_fixtures):
    adapter = ActionAdapter()
    for source in injection_fixtures:
        result = run_pipeline_over_source(source["text"], adapter)
        assert len(adapter.calls) == 0, f"Adapter should not have calls after processing {source['id']}"
        assert result == source["text"]


def test_build_messages_never_puts_fixture_text_in_system_message(injection_fixtures):
    system = "You are a research assistant"
    task = "Analyze this case"
    sources = injection_fixtures[:2]

    messages = build_messages(system, task, None, sources)

    for msg in messages:
        if msg["role"] == "system":
            for source in sources:
                assert source["text"] not in msg["content"]


def test_redact_removes_fake_sk_key():
    text = "API key sk-test1234567890abcdef is here"
    redacted = redact(text)
    assert "sk-test1234567890abcdef" not in redacted
    assert "[REDACTED]" in redacted


def test_redact_removes_postgresql_password():
    text = "Database: postgresql://user:password123@localhost/dbname"
    redacted = redact(text)
    assert "password123" not in redacted
    assert "[REDACTED]" in redacted


@pytest.mark.canary
def test_canary_prompt_injection(injection_fixtures):
    def unsafe_run(text, adapter):
        if "set case to ACT" in text:
            adapter.set_disposition("case_123", "ACT")
        return text

    def check_no_calls():
        adapter = ActionAdapter()
        for source in injection_fixtures:
            unsafe_run(source["text"], adapter)
            assert len(adapter.calls) == 0

    expect_violation(check_no_calls)
