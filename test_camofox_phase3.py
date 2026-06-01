"""Phase 3: after a full camofox restart, verify cookie is still there.

Use the SAME userId derived in test_camofox_persistence.py and look for
the same cookie. If it's there, the on-disk profile survived.
"""
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.browser_camofox_state import get_camofox_identity  # noqa: E402

CAMOFOX = "http://127.0.0.1:9377"
EXPECTED_COOKIE = "hermes_persist_test"
EXPECTED_VALUE = sys.argv[1] if len(sys.argv) > 1 else None


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def camofox(method, path, body=None, params=None, timeout=30):
    fn = {"GET": requests.get, "POST": requests.post, "DELETE": requests.delete}[method]
    r = fn(f"{CAMOFOX}{path}", json=body, params=params, timeout=timeout)
    if r.status_code >= 400:
        log(f"  ! HTTP {r.status_code} on {method} {path}: {r.text[:200]!r}")
    r.raise_for_status()
    return r.json() if r.content else {}


def wait_for_camofox(timeout=30):
    log(f"Waiting for camofox at {CAMOFOX} (max {timeout}s)...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{CAMOFOX}/health", timeout=2)
            if r.status_code == 200:
                log(f"  camofox up: {r.json()}")
                return True
        except Exception:
            pass
        time.sleep(1)
    log("  camofox did not come up in time")
    return False


def main():
    if not wait_for_camofox():
        sys.exit(2)

    identity = get_camofox_identity("persistence_test")
    user_id = identity["user_id"]
    session_key = identity["session_key"]
    log(f"user_id = {user_id}  (same as Phase 1+2)")

    # Create tab and navigate to cookie viewer
    log("Creating new tab and reading cookies...")
    tab = camofox("POST", "/tabs", body={
        "userId": user_id,
        "sessionKey": session_key,
        "url": "https://httpbin.org/cookies",
    }, timeout=60)
    tab_id = tab.get("tabId")
    log(f"  tabId = {tab_id}")

    # Snapshot to see cookies
    snap = camofox("GET", f"/tabs/{tab_id}/snapshot",
                   params={"userId": user_id})
    snapshot_text = snap.get("snapshot", "")
    log(f"  snapshot (first 400 chars):\n    {snapshot_text[:400].replace(chr(10), ' ')}")

    has_name = EXPECTED_COOKIE in snapshot_text
    has_value = EXPECTED_VALUE is None or EXPECTED_VALUE in snapshot_text

    log("")
    log(f"  Cookie name '{EXPECTED_COOKIE}' present: {has_name}")
    if EXPECTED_VALUE:
        log(f"  Cookie value '{EXPECTED_VALUE}' present: {has_value}")

    if has_name and has_value:
        log(f"\n=== Phase 3 RESULT: PASS — cookie survived camofox restart ===")
        sys.exit(0)
    else:
        log(f"\n=== Phase 3 RESULT: FAIL — cookie did NOT survive restart ===")
        log("    This means managed_persistence works within a session but")
        log("    the on-disk profile is not being persisted across restarts.")
        log("    (Either camofox doesn't persist, or our userId mapping is wrong.)")
        sys.exit(1)


if __name__ == "__main__":
    main()
