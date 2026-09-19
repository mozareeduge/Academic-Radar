"""Static checks for RC smoke test setup.

Verifies that docker-compose.yml, scripts/rc_smoke.py, CI config, and
environment examples are correctly configured for release-candidate testing.
"""
import os
import sys
import yaml
from pathlib import Path


def test_docker_compose_parses():
    """docker-compose.yml must be valid YAML."""
    compose_path = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"
    assert compose_path.exists(), f"docker-compose.yml not found at {compose_path}"

    with open(compose_path) as f:
        config = yaml.safe_load(f)

    assert config is not None, "docker-compose.yml is empty or malformed"
    assert "services" in config, "docker-compose.yml missing 'services' key"


def test_docker_compose_has_radar_worker():
    """docker-compose.yml must contain radar-worker service."""
    compose_path = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"

    with open(compose_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})
    assert "radar-worker" in services, "radar-worker service not found in docker-compose.yml"

    worker = services["radar-worker"]
    assert "image" in worker or "build" in worker, "radar-worker has no image or build"
    assert "command" in worker, "radar-worker has no command"

    # Should run rq worker on discovery, research, watch queues
    command = worker.get("command", [])
    assert "rq" in command or any("rq" in str(c) for c in command), \
        "radar-worker command does not include 'rq'"


def test_rc_smoke_script_exists_and_compiles():
    """scripts/rc_smoke.py must exist and compile."""
    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "rc_smoke.py"
    assert script_path.exists(), f"rc_smoke.py not found at {script_path}"

    # Check it compiles
    with open(script_path) as f:
        code = f.read()

    try:
        compile(code, str(script_path), "exec")
    except SyntaxError as e:
        raise AssertionError(f"rc_smoke.py has syntax error: {e}")


def test_ci_yml_has_compose_smoke_job():
    """CI job 'compose-smoke' must exist in .github/workflows/ci.yml."""
    ci_path = Path(__file__).parent.parent.parent.parent / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), f"ci.yml not found at {ci_path}"

    with open(ci_path) as f:
        config = yaml.safe_load(f)

    jobs = config.get("jobs", {})
    assert "compose-smoke" in jobs, "compose-smoke job not found in ci.yml"

    job = jobs["compose-smoke"]
    assert "runs-on" in job, "compose-smoke job missing 'runs-on'"
    assert "steps" in job, "compose-smoke job missing 'steps'"

    # Should have compose up, smoke test, verify-durable
    step_names = []
    for step in job.get("steps", []):
        if "name" in step:
            step_names.append(step["name"].lower())

    assert any("compose" in name or "stack" in name for name in step_names), \
        f"compose-smoke job should include 'Start compose stack' or similar. Found: {step_names}"
    assert any("smoke" in name for name in step_names), \
        f"compose-smoke job should include a smoke test step. Found: {step_names}"


def test_env_example_has_no_credential_values():
    """All credential/token/key/password variables in .env.example must be empty."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env.example"
    assert env_path.exists(), f".env.example not found at {env_path}"

    secret_keywords = {"KEY", "SECRET", "TOKEN", "PASSWORD"}

    with open(env_path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments
            if line.startswith("#"):
                continue

            if "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Check if this is a secret variable
            if any(keyword in key.upper() for keyword in secret_keywords):
                # Should be empty (just key=)
                assert value == "", \
                    f".env.example line {line_num}: {key} has value '{value}', " \
                    f"secrets must be empty (set at runtime)"


def test_api_imports_radar_dev():
    """api/app.py must import and register radar_dev router."""
    app_path = Path(__file__).parent.parent.parent / "api" / "app.py"
    assert app_path.exists(), f"api/app.py not found at {app_path}"

    with open(app_path) as f:
        content = f.read()

    assert "radar_dev" in content, \
        "api/app.py does not import radar_dev"
    assert "include_router(radar_dev.router)" in content, \
        "api/app.py does not register radar_dev router"


def test_radar_dev_module_exists():
    """api/routes/radar_dev.py must exist."""
    dev_path = Path(__file__).parent.parent.parent / "api" / "routes" / "radar_dev.py"
    assert dev_path.exists(), f"radar_dev.py not found at {dev_path}"

    # Check it compiles
    with open(dev_path) as f:
        code = f.read()

    try:
        compile(code, str(dev_path), "exec")
    except SyntaxError as e:
        raise AssertionError(f"radar_dev.py has syntax error: {e}")


def test_radar_runbook_exists():
    """docs/RADAR_RUNBOOK.md must document start, migrate, import, backup/restore."""
    runbook_path = Path(__file__).parent.parent.parent.parent / "docs" / "RADAR_RUNBOOK.md"
    assert runbook_path.exists(), f"RADAR_RUNBOOK.md not found at {runbook_path}"

    with open(runbook_path) as f:
        content = f.read().lower()

    # Check for key sections
    assert "starting" in content or "start" in content, \
        "RADAR_RUNBOOK.md missing 'Starting' section"
    assert "migration" in content, \
        "RADAR_RUNBOOK.md missing database migration documentation"
    assert "seed" in content or "import" in content, \
        "RADAR_RUNBOOK.md missing seed import documentation"
    assert "backup" in content or "restore" in content, \
        "RADAR_RUNBOOK.md missing backup/restore documentation"
