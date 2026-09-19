import hashlib
from academic_radar.security.redact import redact


def make_run_identity(
    model_id: str,
    provider_id: str,
    prompt_text: str,
    schema_version: str,
    protocol_version: str,
    run_id: str,
) -> dict:
    """Create a run identity dict with hashed prompt and metadata.

    Args:
        model_id: The LLM model identifier.
        provider_id: The provider identifier.
        prompt_text: The full prompt text.
        schema_version: Schema version string.
        protocol_version: Protocol version string.
        run_id: Unique run identifier.

    Returns:
        Dict with model_id, provider_id, prompt_hash, schema_version,
        protocol_version, and run_id. Contains NO secrets.
    """
    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()

    return {
        "model_id": model_id,
        "provider_id": provider_id,
        "prompt_hash": prompt_hash,
        "schema_version": schema_version,
        "protocol_version": protocol_version,
        "run_id": run_id,
    }


def assert_no_secrets(identity: dict) -> None:
    """Assert that identity dict contains no secrets.

    Checks all values against redact patterns.

    Raises AssertionError if any value would be redacted.
    """
    for key, value in identity.items():
        if value is None or not isinstance(value, str):
            continue
        redacted = redact(value)
        if redacted != value:
            raise AssertionError(
                f"Identity field '{key}' contains secrets that would be redacted"
            )
