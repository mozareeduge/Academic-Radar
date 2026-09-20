"""Local reproduction of the CI compose smoke test (no Docker needed).

Starts the API with uvicorn on 127.0.0.1:8000 in fixture mode against a temporary SQLite file,
runs scripts/rc_smoke.py, restarts the API on the SAME database file, then runs
scripts/rc_smoke.py --verify-durable. Exit code 0 only if both runs pass.
"""
import http.client
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def start(db_path, log_path):
    env = dict(os.environ, ASTRA_SECRET_KEY="local-smoke-" + "x" * 40, RADAR_FIXTURE_MODE="1",
               DATABASE_URL="sqlite:///" + str(db_path).replace("\\", "/"))
    log = open(log_path, "ab")
    return subprocess.Popen([PY, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8000"],
                            cwd=ROOT / "astra", env=env, stdout=log, stderr=subprocess.STDOUT)


def wait_health(timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        try:
            c = http.client.HTTPConnection("127.0.0.1", 8000, timeout=3)
            c.request("GET", "/health")
            if c.getresponse().status == 200:
                return True
        except OSError:
            pass
        time.sleep(1)
    return False


def stop(p):
    p.terminate()
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="radar-smoke-"))
    db, log = tmp / "astra.db", tmp / "server.log"
    failed = False
    p = start(db, log)
    try:
        if not wait_health():
            print("API did not become healthy; server log tail:")
            print(log.read_text(errors="replace")[-3000:])
            return 1
        rc1 = subprocess.run([PY, str(ROOT / "scripts" / "rc_smoke.py")], cwd=ROOT).returncode
        failed = rc1 != 0
    finally:
        stop(p)
    if not failed:
        p = start(db, log)
        try:
            if not wait_health():
                print("API did not restart; server log tail:")
                print(log.read_text(errors="replace")[-3000:])
                return 1
            rc2 = subprocess.run([PY, str(ROOT / "scripts" / "rc_smoke.py"), "--verify-durable"], cwd=ROOT).returncode
            failed = rc2 != 0
        finally:
            stop(p)
    if not failed:
        stage = sys.argv[sys.argv.index("--stage") + 1] if "--stage" in sys.argv else "all"
        rc3 = subprocess.run([PY, str(ROOT / "scripts" / "smoke_assertions.py"), str(db), "--stage", stage],
                             cwd=ROOT).returncode
        failed = rc3 != 0
    if failed:
        print("--- server log tail ---")
        print(log.read_text(errors="replace")[-3000:])
        return 1
    print("LOCAL SMOKE OK (fresh run + restart + durable check + database assertions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
