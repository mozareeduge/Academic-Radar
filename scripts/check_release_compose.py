"""Assert that the rendered production Compose graph matches the RC contract.

Input is `docker compose -f docker-compose.yml -f docker-compose.prod.yml
--profile redis config --format json`. The CI job also builds and starts these
services; this check makes missing dependencies or fixture settings visible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def check(config: dict, sha: str) -> None:
    services = config.get("services", {})
    required = {"api", "radar-worker", "dashboard", "redis", "caddy"}
    missing = required - services.keys()
    if missing:
        raise ValueError(f"Missing production services: {sorted(missing)}")

    for name, image in {
        "api": "astra-api",
        "radar-worker": "astra-radar-worker",
        "dashboard": "astra-dashboard",
    }.items():
        actual = services[name].get("image")
        if actual != f"{image}:{sha}":
            raise ValueError(f"{name} image is not tagged with candidate SHA: {actual}")
        if "no-new-privileges:true" not in services[name].get("security_opt", []):
            raise ValueError(f"{name} lacks no-new-privileges")
        if "ALL" not in services[name].get("cap_drop", []):
            raise ValueError(f"{name} retains capabilities")

    api_env = services["api"].get("environment", {})
    worker_env = services["radar-worker"].get("environment", {})
    if not api_env.get("RADAR_OWNER_EMAIL"):
        raise ValueError("Radar owner is not configured in the API container")
    for name, env in (("api", api_env), ("radar-worker", worker_env)):
        if str(env.get("RADAR_FIXTURE_MODE")) != "0":
            raise ValueError(f"{name} is running in fixture mode")

    def dependency(service: str, target: str, condition: str) -> None:
        actual = services[service].get("depends_on", {}).get(target, {}).get("condition")
        if actual != condition:
            raise ValueError(f"{service} must wait for {target} ({condition}); got {actual}")

    dependency("radar-worker", "redis", "service_healthy")
    dependency("dashboard", "api", "service_healthy")
    dependency("caddy", "api", "service_healthy")
    dependency("caddy", "dashboard", "service_started")
    command = services["radar-worker"].get("command", [])
    if not all(queue in command for queue in ("discovery", "research", "watch")):
        raise ValueError("Radar worker does not consume all three queues")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_release_compose.py CONFIG_JSON CANDIDATE_SHA")
    try:
        check(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2])
    except (OSError, ValueError) as exc:
        raise SystemExit(f"RELEASE OVERLAY FAILED: {exc}") from exc
    print("RELEASE OVERLAY OK")
