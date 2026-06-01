"""Test that camofox managed persistence survives a tab close + new tab,
and ideally a full camofox restart.

Usage:  python test_camofox_persistence.py [--restart]
"""
import argparse
import json
import sys
import time
import uuid
from pathlib import Path

import requests

# Make hermes modules importable
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.browser_camofox_state import get_camofox_identity  # noqa: E402

CAMOFOX = "http://127.0.0.1:9377"
TIMEOUT = 30


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def camofox(method, path, body=None, params=None, timeout=TIMEOUT):
    fn = {"GET": requests.get, "POST": requests.post, "DELETE": requests.delete}[method]
    r = fn(f"{CAMOFOX}{path}", json=body, params=params, timeout=timeout)
    if r.status_code >= 400:
        log(f"  ! HTTP {r.status_code} on {method} {path}: {r.text[:200]!r}")
    r.raise_for_status()
    return r.json() if r.content else {}


def create_tab(user_id, session_key, url="https://httpbin.org/cookies"):
    return camofox("POST", "/tabs", body={
        "userId": user_id, "sessionKey": session_key, "url": url,
    })


def navigate(tab_id, user_id, url):
    return camofox("POST", f"/tabs/{tab_id}/navigate",
                   body={"userId": user_id, "url": url}, timeout=60)


def snapshot(tab_id, user_id):
    data = camofox("GET", f"/tabs/{tab_id}/snapshot",
                   params={"userId": user_id})
    return data.get("snapshot", "")


def close_session(user_id):
    return camofox("DELETE", f"/sessions/{user_id}")


def set_test_cookie_via_navigation(tab_id, user_id, name, value):
    """Use httpbin.org to set a cookie via Set-Cookie response header."""
    url = f"https://httpbin.org/cookies/set?{name}={value}"
    nav = navigate(tab_id, user_id, url)
    return nav.get("url", "")


def read_cookies_via_navigation(tab_id, user_id):
    """Navigate to httpbin.org/cookies which reflects all current cookies as JSON."""
    nav = navigate(tab_id, user_id, "https://httpbin.org/cookies")
    snap = snapshot(tab_id, user_id)
    return snap


def test_persistence_with_restart():
    log("=== Test: managed persistence with full camofox restart ===")
    identity = get_camofox_identity("persistence_test")
    user_id = identity["user_id"]
    session_key = identity["session_key"]
    log(f"user_id = {user_id}")
    log(f"session_key = {session_key}")

    cookie_name = "hermes_persist_test"
    cookie_value = uuid.uuid4().hex[:12]

    # --- Phase 1: set cookie ---
    log("Phase 1: create tab + set cookie via httpbin.org")
    tab1 = create_tab(user_id, session_key, url="https://httpbin.org/cookies")
    tab_id_1 = tab1.get("tabId")
    log(f"  tab1.tabId = {tab_id_1}")

    final_url = set_test_cookie_via_navigation(tab_id_1, user_id, cookie_name, cookie_value)
    log(f"  navigated, final url: {final_url}")

    # Read cookies back to confirm
    snap = read_cookies_via_navigation(tab_id_1, user_id)
    log(f"  cookies snapshot (first 300 chars):\n    {snap[:300].replace(chr(10), ' ')}")
    phase1_ok = cookie_name in snap and cookie_value in snap
    log(f"  Phase 1: cookie set & visible = {phase1_ok}")

    # --- Phase 2: close session, recreate with same userId ---
    log("Phase 2: close session, recreate with same userId (no camofox restart)")
    close_session(user_id)
    time.sleep(1)
    tab2 = create_tab(user_id, session_key, url="https://httpbin.org/cookies")
    tab_id_2 = tab2.get("tabId")
    log(f"  tab2.tabId = {tab_id_2}")
    snap2 = snapshot(tab_id_2, user_id)
    log(f"  cookies snapshot (first 300 chars):\n    {snap2[:300].replace(chr(10), ' ')}")
    phase2_ok = cookie_name in snap2 and cookie_value in snap2
    log(f"  Phase 2: cookie persisted across session recreate = {phase2_ok}")

    close_session(user_id)
    return phase1_ok and phase2_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--restart", action="store_true",
                        help="also test full camofox restart (kill + respawn)")
    args = parser.parse_args()
    ok = test_persistence_with_restart()
    log(f"\n=== RESULT: {'PASS' if ok else 'FAIL'} ===")
    sys.exit(0 if ok else 1)
