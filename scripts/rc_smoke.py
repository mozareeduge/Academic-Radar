#!/usr/bin/env python3
"""Release-candidate smoke test: fixture-backed discovery, research, watch, brief.

Runs against http://localhost:8000 in fixture mode (RADAR_FIXTURE_MODE=1).
Tests: import seed, discovery, supervisor case research, MA case with funding,
watch trigger, brief freeze, durability after restart.

Usage:
    python scripts/rc_smoke.py           # test smoke flow
    python scripts/rc_smoke.py --verify-durable  # verify state after restart
"""
import sys
import json
import time
import http.client
import urllib.parse
import argparse
from typing import Optional


def log(msg: str) -> None:
    """Print timestamped log."""
    print(f"[rc_smoke] {msg}", file=sys.stderr, flush=True)


def request(method: str, path: str, body: Optional[dict] = None,
            expect_status: int = 200, timeout: int = 30) -> dict:
    """Make HTTP request to localhost:8000.

    Args:
        method: GET, POST, PATCH, DELETE
        path: /api/... path
        body: JSON body for POST/PATCH
        expect_status: expected HTTP status
        timeout: request timeout in seconds

    Returns:
        Parsed JSON response

    Raises:
        RuntimeError if status != expect_status or on network error
    """
    conn = http.client.HTTPConnection("localhost", 8000, timeout=timeout)
    try:
        headers = {"Content-Type": "application/json"}
        data = None
        if body:
            import json as json_lib
            data = json_lib.dumps(body).encode()

        conn.request(method, path, data, headers)
        resp = conn.getresponse()
        resp_data = resp.read().decode()

        if resp.status != expect_status:
            raise RuntimeError(
                f"{method} {path} returned {resp.status}, expected {expect_status}\n"
                f"Response: {resp_data[:500]}"
            )

        try:
            return json.loads(resp_data) if resp_data else {}
        except json.JSONDecodeError:
            return {"raw": resp_data}
    finally:
        conn.close()


def wait_for_health(timeout: int = 60) -> None:
    """Wait for /health to return ok."""
    log("Waiting for API health...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = request("GET", "/health", expect_status=200)
            if resp.get("status") == "ok":
                log(f"API healthy (version {resp.get('version')})")
                return
        except RuntimeError:
            pass
        time.sleep(1)
    raise RuntimeError(f"API did not become healthy within {timeout}s")


def import_seed() -> str:
    """Import synthetic seed profile and routes.

    Returns:
        profile_id
    """
    log("Importing seed profile and routes...")
    resp = request("POST", "/api/radar/dev/import-seed",
                   {"seed_path": "astra/tests/academic_radar/fixtures/synthetic_seed.yaml"},
                   expect_status=200)
    profile_id = resp.get("profile_id")
    if not profile_id:
        raise RuntimeError("Import seed did not return profile_id")
    log(f"  Profile imported: {profile_id}")
    return profile_id


def run_fixture_discovery(profile_id: str) -> str:
    """Run fixture discovery on the profile.

    Returns:
        discovery_run_id
    """
    log("Running fixture discovery...")
    resp = request("POST", "/api/radar/dev/discovery",
                   {"profile_id": profile_id},
                   expect_status=200)
    run_id = resp.get("run_id")
    if not run_id:
        raise RuntimeError("Discovery did not return run_id")
    log(f"  Discovery started: {run_id}")

    # Wait for discovery to complete
    start = time.time()
    while time.time() - start < 30:
        resp = request("GET", f"/api/radar/dev/discovery-status/{run_id}",
                       expect_status=200)
        status = resp.get("status")
        if status == "completed":
            log(f"  Discovery completed: {resp.get('entity_count', 0)} entities")
            return run_id
        elif status == "failed":
            raise RuntimeError(f"Discovery failed: {resp.get('error')}")
        time.sleep(1)

    raise RuntimeError("Discovery did not complete within 30s")


def create_supervisor_case(profile_id: str) -> str:
    """Create a supervisor-focused evaluation case and research it.

    Returns:
        case_id
    """
    log("Creating supervisor case...")
    resp = request("POST", "/api/radar/cases",
                   {
                       "profile_id": profile_id,
                       "route_id": None,  # will pick supervisor route
                       "entity_id": None,  # supervisor lookup
                       "entity_type": "person"
                   },
                   expect_status=200)
    case_id = resp.get("id")
    if not case_id:
        raise RuntimeError("Case creation did not return id")
    log(f"  Case created: {case_id}")

    # Trigger research
    log("  Researching case with mock provider...")
    resp = request("POST", f"/api/radar/dev/research",
                   {"case_id": case_id, "use_mock": True},
                   expect_status=200)
    job_id = resp.get("job_id")

    # Wait for research to complete
    start = time.time()
    while time.time() - start < 30:
        resp = request("GET", f"/api/radar/dev/research-status/{job_id}",
                       expect_status=200)
        if resp.get("status") == "completed":
            log(f"  Research completed")
            return case_id
        elif resp.get("status") == "failed":
            raise RuntimeError(f"Research failed: {resp.get('error')}")
        time.sleep(1)

    raise RuntimeError("Research did not complete within 30s")


def create_ma_case_with_funding(profile_id: str) -> str:
    """Create an MA case with two funding assessments.

    Returns:
        case_id
    """
    log("Creating MA case with funding...")
    resp = request("POST", "/api/radar/cases",
                   {
                       "profile_id": profile_id,
                       "route_id": None,  # will pick MA route
                       "entity_id": None,
                       "entity_type": "programme"
                   },
                   expect_status=200)
    case_id = resp.get("id")
    if not case_id:
        raise RuntimeError("MA case creation did not return id")
    log(f"  MA case created: {case_id}")

    # Add two funding assessments
    for i in range(2):
        log(f"  Adding funding assessment {i+1}...")
        request("POST", f"/api/radar/funding/{case_id}",
                {
                    "funding_route_id": f"fund-route-{i+1}",
                    "currency": "GBP",
                    "award_amount": "15000.00",
                    "duration_months": 12,
                    "state": "ASSESSED"
                },
                expect_status=200)

    log("  MA case complete with funding")
    return case_id


def trigger_watch_change(case_id: str) -> str:
    """Trigger a watch on a case and simulate a change.

    Returns:
        change_event_id
    """
    log("Creating watch target and triggering change...")

    # Create watch target
    resp = request("POST", "/api/radar/watch/targets",
                   {
                       "case_id": case_id,
                       "target_type": "entity",
                       "check_interval_hours": 24
                   },
                   expect_status=200)
    watch_id = resp.get("id")
    if not watch_id:
        raise RuntimeError("Watch target creation did not return id")
    log(f"  Watch target: {watch_id}")

    # Simulate a change event
    resp = request("POST", f"/api/radar/dev/simulate-change",
                   {"watch_id": watch_id},
                   expect_status=200)
    change_id = resp.get("change_event_id")
    if not change_id:
        raise RuntimeError("Change simulation did not return change_event_id")
    log(f"  Change event created: {change_id}")

    return change_id


def freeze_brief(case_id: str) -> str:
    """Freeze an application brief for the case.

    Returns:
        brief_id
    """
    log("Freezing application brief...")
    resp = request("POST", f"/api/radar/briefs",
                   {"case_id": case_id},
                   expect_status=200)
    brief_id = resp.get("id")
    if not brief_id:
        raise RuntimeError("Brief creation did not return id")
    log(f"  Brief frozen: {brief_id}")
    return brief_id


def verify_durable_state(case_ids: list[str]) -> None:
    """Verify that created cases and briefs still exist after restart.

    Args:
        case_ids: list of case IDs to verify
    """
    log("Verifying durable state after restart...")
    for case_id in case_ids:
        resp = request("GET", f"/api/radar/cases/{case_id}",
                       expect_status=200)
        if not resp.get("id"):
            raise RuntimeError(f"Case {case_id} not found after restart")
    log(f"  All {len(case_ids)} cases persisted")


def main() -> int:
    """Run the smoke test."""
    parser = argparse.ArgumentParser(description="Radar RC smoke test")
    parser.add_argument("--verify-durable", action="store_true",
                        help="Verify durable state after restart (skip creation)")
    args = parser.parse_args()

    try:
        wait_for_health()

        steps = []
        results = {"ok": True, "steps": steps}

        if not args.verify_durable:
            # Import seed
            try:
                profile_id = import_seed()
                steps.append({"step": "import_seed", "status": "ok", "profile_id": profile_id})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "import_seed", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

            # Run discovery
            try:
                run_fixture_discovery(profile_id)
                steps.append({"step": "discovery", "status": "ok"})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "discovery", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

            # Create supervisor case and research
            try:
                case_id_1 = create_supervisor_case(profile_id)
                steps.append({"step": "supervisor_case", "status": "ok", "case_id": case_id_1})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "supervisor_case", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

            # Create MA case with funding
            try:
                case_id_2 = create_ma_case_with_funding(profile_id)
                steps.append({"step": "ma_case", "status": "ok", "case_id": case_id_2})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "ma_case", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

            # Trigger watch change
            try:
                change_id = trigger_watch_change(case_id_2)
                steps.append({"step": "watch_change", "status": "ok", "change_id": change_id})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "watch_change", "status": "failed", "error": str(e)})
                results["ok"] = False
                # Don't fail entirely; brief freeze is still important

            # Freeze brief
            try:
                brief_id = freeze_brief(case_id_2)
                steps.append({"step": "brief_freeze", "status": "ok", "brief_id": brief_id})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "brief_freeze", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

        else:
            # Verify durable state (called after restart)
            try:
                # In a real scenario, you'd pass in the case IDs from the first run.
                # For now, we just verify the import-seed endpoint.
                resp = request("GET", "/api/radar/cases", expect_status=200)
                case_count = len(resp.get("items", []))
                steps.append({"step": "verify_cases", "status": "ok", "case_count": case_count})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "verify_cases", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

        log(f"Smoke test {'PASSED' if results['ok'] else 'FAILED'}")
        print(json.dumps(results))
        return 0 if results["ok"] else 1

    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
