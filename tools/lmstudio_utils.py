"""
LM Studio utilities — model listing, auto-sync, URL auto-detection on Windows.
"""

import json
import logging
import os
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


# Module-level session for connection pooling on the LM Studio hot path
# (called before every API request — reusing TCP connections avoids
# half-open socket accumulation under retry storms when LM Studio is
# offline). Memory leak fix: bare `requests.get()` leaks the underlying
# socket if the call site raises between get() and json().
_http_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Lazy-init a module-level requests.Session with retry config."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.headers.update({"Content-Type": "application/json"})
    return _http_session


def list_models(base_url: str) -> list[dict]:
    """Fetch all models from LM Studio's v0 models endpoint."""
    api_base = base_url.rstrip("/").replace("/v1", "").replace("/chat/completions", "")
    url = f"{api_base}/api/v0/models"
    try:
        resp = _get_session().get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except requests.RequestException as e:
        logger.debug("LM Studio list_models failed for %s: %s", url, e)
        return []


def get_loaded_model(base_url: str) -> Optional[str]:
    """
    Return the **last** (most recently) loaded model from LM Studio,
    or ``None`` if no models are loaded.

    Changed from ``models[0]`` (first) to ``models[-1]`` (last) so that
    when the user switches models, we honour their most recent selection.
    """
    all_models = list_models(base_url)
    loaded = [m["id"] for m in all_models if m.get("state") == "loaded"]
    return loaded[-1] if loaded else None


def auto_update_model_from_response(model_name: str) -> None:
    """Write *model_name* to the user's ``config.yaml`` (both ``default`` and ``current``)."""
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    config_path = hermes_home / "config.yaml"
    if not config_path.exists():
        return
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        if "model" not in cfg:
            cfg["model"] = {}
        cfg["model"]["default"] = model_name
        cfg["model"]["current"] = model_name
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
        logger.info("Auto-updated config.yaml model to %s", model_name)
    except Exception as e:
        logger.debug("Failed to auto-update config.yaml: %s", e)


def fix_config_url() -> None:
    """
    On Windows, if LM Studio's configured ``base_url`` is not reachable,
    try to find LM Studio's actual API URL and update ``config.yaml``.

    LM Studio typically listens on ``http://127.0.0.1:1234`` or
    ``http://localhost:1234``.  If the configured URL doesn't respond,
    auto-detect which one works.
    """
    if os.name != "nt":
        return
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    config_path = hermes_home / "config.yaml"
    if not config_path.exists():
        return
    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        current_url = (cfg.get("model") or {}).get("base_url", "")
        if current_url and _is_url_reachable(current_url):
            return  # configured URL works — nothing to do
        candidates = ["http://127.0.0.1:1234", "http://localhost:1234"]
        for candidate in candidates:
            if _is_url_reachable(candidate + "/v1/models"):
                cfg["model"]["base_url"] = candidate + "/v1"
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
                logger.info("Auto-detected LM Studio URL: %s", candidate + "/v1")
                return
    except Exception as e:
        logger.debug("LM Studio URL fix failed: %s", e)


def _is_url_reachable(url: str, timeout: float = 3.0) -> bool:
    """Check if *url* responds within *timeout* seconds."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 1234
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
