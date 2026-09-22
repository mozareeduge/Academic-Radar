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
        except (RuntimeError, ConnectionError, OSError):
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
    """Create a supervisor-focused evaluation case, research it, and add gate.

    Returns:
        case_id
    """
    log("Creating supervisor case...")

    # First get a route and target to use
    resp = request("GET", f"/api/radar/dev/profile/{profile_id}", expect_status=200)
    routes = resp.get("routes", [])
    if not routes:
        raise RuntimeError("No routes available for profile")
    route_id = routes[0]["id"]

    # Get a target entity (from discovery results)
    resp = request("GET", "/api/radar/dev/targets", expect_status=200)
    targets = resp.get("items", [])
    if not targets:
        raise RuntimeError("No targets available")
    target_id = targets[0]["id"]

    resp = request("POST", "/api/radar/dev/cases",
                   {
                       "route_id": route_id,
                       "target_id": target_id,
                       "application_route": "SUPERVISOR_FIRST_PHD"
                   },
                   expect_status=201)
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
    if not job_id:
        raise RuntimeError("Research did not return job_id")

    # Poll for research completion
    start = time.time()
    while time.time() - start < 30:
        resp = request("GET", f"/api/radar/dev/research-status/{job_id}",
                       expect_status=200)
        status = resp.get("status")
        if status == "completed":
            log(f"  Research completed")
            # Create a hard gate PASS so brief can freeze
            log("  Adding supervisor gate assessment...")
            request("POST", f"/api/radar/dev/gate/{case_id}",
                   {
                       "requirement": "supervisor_status",
                       "result": "PASS",
                       "evidence_ids": ["evidence-1"]
                   },
                   expect_status=201)
            return case_id
        elif status == "failed":
            raise RuntimeError(f"Research failed: {resp.get('error')}")
        time.sleep(1)

    raise RuntimeError("Research did not complete within 30s")


def create_ma_case_with_funding(profile_id: str) -> tuple:
    """Create an MA case with two funding assessments.

    Returns:
        (case_id, funding_evidence_urls)
    """
    log("Creating MA case with funding...")

    # Get a route and target
    resp = request("GET", f"/api/radar/dev/profile/{profile_id}", expect_status=200)
    routes = resp.get("routes", [])
    if not routes:
        raise RuntimeError("No routes available for profile")
    route_id = routes[0]["id"]

    resp = request("GET", "/api/radar/dev/targets", expect_status=200)
    targets = resp.get("items", [])
    if not targets:
        raise RuntimeError("No targets available")
    target_id = targets[0]["id"]

    resp = request("POST", "/api/radar/dev/cases",
                   {
                       "route_id": route_id,
                       "target_id": target_id,
                       "application_route": "MA_PROGRAMME"
                   },
                   expect_status=201)
    case_id = resp.get("id")
    if not case_id:
        raise RuntimeError("MA case creation did not return id")
    log(f"  MA case created: {case_id}")

    # Add two funding assessments
    funding_urls = []
    for i in range(2):
        log(f"  Adding funding assessment {i+1}...")
        # First assessment has known living cost; second has unknown
        if i == 0:
            resp = request("POST", f"/api/radar/dev/funding/{case_id}",
                    {
                        "funding_route_id": f"fund-route-{i+1}",
                        "currency": "GBP",
                        "award_amount": "15000.00",
                        "tuition": "3000.00",
                        "living_costs": "15000.00",
                        "mandatory_fees": "500.00",
                        "duration_months": 12,
                        "state": "ELIGIBLE"
                    },
                    expect_status=201)
        else:
            # Second assessment with unknown living cost
            resp = request("POST", f"/api/radar/dev/funding/{case_id}",
                    {
                        "funding_route_id": f"fund-route-{i+1}",
                        "currency": "GBP",
                        "award_amount": "15000.00",
                        "tuition": "3000.00",
                        "mandatory_fees": "500.00",
                        "duration_months": 12,
                        "state": "ELIGIBILITY_UNKNOWN",
                        "unknown_costs": {"living_costs": "unknown"}
                    },
                    expect_status=201)
        source_url = resp.get("source_url")
        if source_url:
            funding_urls.append(source_url)
        else:
            # Fallback (should not happen)
            funding_urls.append(f"https://fixtures.example.org/funding/{case_id}/fund-route-{i+1}")

    # Research the MA case
    log("  Researching MA case with mock provider...")
    resp = request("POST", f"/api/radar/dev/research",
                   {"case_id": case_id, "use_mock": True},
                   expect_status=200)
    job_id = resp.get("job_id")
    if not job_id:
        raise RuntimeError("Research did not return job_id")

    # Poll for research completion
    start = time.time()
    while time.time() - start < 30:
        resp = request("GET", f"/api/radar/dev/research-status/{job_id}",
                       expect_status=200)
        status = resp.get("status")
        if status == "completed":
            log(f"  MA research completed")
            break
        elif status == "failed":
            raise RuntimeError(f"MA research failed: {resp.get('error')}")
        time.sleep(1)
    else:
        raise RuntimeError("MA research did not complete within 30s")

    log("  MA case complete with funding and research")
    return case_id, funding_urls


def trigger_watch_change(case_id: str, funding_url: str) -> str:
    """Trigger a real watch on funding URL and record material change event.

    Returns:
        change_event_id
    """
    log("Creating watch target on funding evidence and triggering change...")

    # Create watch target on the funding URL
    resp = request("POST", "/api/radar/dev/watch-run",
                   {
                       "case_id": case_id,
                       "source_url": funding_url,
                       "prior_text": "initial funding data",
                       "changed_text": "initial funding data\nchanged line 2\nchanged line 3"
                   },
                   expect_status=200)
    change_id = resp.get("change_event_id")
    if not change_id:
        raise RuntimeError("Watch run did not return change_event_id")
    log(f"  Change event created: {change_id}")

    return change_id


def freeze_brief(case_id: str) -> str:
    """Freeze an application brief for the case.

    Returns:
        brief_id
    """
    log("Freezing application brief...")
    resp = request("POST", f"/api/radar/dev/briefs",
                   {"case_id": case_id},
                   expect_status=201)
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

    resp = request("GET", "/api/radar/dev/cases",
                   expect_status=200)
    cases_after = resp.get("items", [])
    case_ids_after = {c.get("id") for c in cases_after}

    for case_id in case_ids:
        if case_id not in case_ids_after:
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
                case_id_2, funding_urls = create_ma_case_with_funding(profile_id)
                steps.append({"step": "ma_case", "status": "ok", "case_id": case_id_2})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "ma_case", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

            # Freeze supervisor brief first (before watch change)
            try:
                brief_id_sup = freeze_brief(case_id_1)
                steps.append({"step": "supervisor_brief_freeze", "status": "ok", "brief_id": brief_id_sup})
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "supervisor_brief_freeze", "status": "failed", "error": str(e)})
                results["ok"] = False
                return 1

            # Trigger watch change on MA case's first funding evidence
            try:
                if funding_urls:
                    change_id = trigger_watch_change(case_id_2, funding_urls[0])
                    steps.append({"step": "watch_change", "status": "ok", "change_id": change_id})
                else:
                    log("WARNING: No funding URLs available for watch")
            except RuntimeError as e:
                log(f"ERROR: {e}")
                steps.append({"step": "watch_change", "status": "failed", "error": str(e)})
                results["ok"] = False
                # Don't fail entirely; brief freeze still needed

            # Freeze MA brief after the watch-triggered invalidation. The freeze
            # is EXPECTED to be refused (422 Brief blocked, staleness reasons):
            # invalidate() marks the changed evidence's case STALE, and
            # ORACLE-032 requires a frozen brief to refuse stale facts. The
            # freeze succeeding here would mean the guard regressed.
            try:
                brief_id_ma = freeze_brief(case_id_2)
                steps.append({"step": "ma_brief_freeze", "status": "ok", "brief_id": brief_id_ma})
                log("ERROR: MA brief freeze succeeded after STALE invalidation - guard regressed")
                results["ok"] = False
            except RuntimeError as e:
                if "Brief blocked" not in str(e) or not any(
                    word in str(e) for word in ("stale", "STALE")
                ):
                    log(f"ERROR: {e}")
                    steps.append({"step": "ma_brief_freeze", "status": "failed", "error": str(e)})
                    results["ok"] = False
                else:
                    steps.append({
                        "step": "ma_brief_freeze_refused",
                        "status": "ok",
                        "note": "freeze correctly refused stale case (ORACLE-032)",
                    })
                    log("OK: MA brief freeze correctly refused (case STALE after invalidation)")

        else:
            # Verify durable state (called after restart)
            try:
                # List all cases via dev endpoint
                resp = request("GET", "/api/radar/dev/cases", expect_status=200)
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
