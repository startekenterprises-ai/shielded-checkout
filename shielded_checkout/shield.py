"""Agent-Shield client (live API).

Agent-Shield is a security gate for AI agents: it scans content an agent is
about to act on — prompt injection, leaked secrets, PII, SSRF-risk URLs —
and returns a verdict plus a signed, verifiable receipt for every scan.

API used here (free tier, self-serve, no email required):
  POST /v1/signup  -> {"api_key": "...", "tier": "free", ...}
  POST /v2/scan    -> {"verdict": "no_signals" | "suspicious" | "malicious",
                       "action": "allow" | "block", "findings": [...],
                       "receipt": {"receipt_id": ..., "signature": ...,
                                   "verify_url": ...}}
Auth is the X-API-Key header.
"""

import json
import os
import urllib.error
import urllib.request

BASE_URL = "https://agent-shield.startekenterprises.com"
_UA = "ShieldedCheckout/1.0 (PayPal AI Hackathon demo)"
_KEY_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".shield_key")


def _post(path, body, api_key=None):
    headers = {"Content-Type": "application/json", "User-Agent": _UA}
    if api_key:
        headers["X-API-Key"] = api_key
    req = urllib.request.Request(
        BASE_URL + path, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


def get_api_key():
    """Return an Agent-Shield API key: env first, then the local cache file,
    then a fresh self-serve signup (free tier: 1,000 scans/day, no email)."""
    key = os.environ.get("AGENT_SHIELD_API_KEY", "").strip()
    if key:
        return key
    if os.path.exists(_KEY_CACHE):
        cached = open(_KEY_CACHE).read().strip()
        if cached:
            return cached
    status, data = _post("/v1/signup", {})
    if status != 200 or not data.get("api_key"):
        raise RuntimeError(f"Agent-Shield signup failed: HTTP {status}: {data}")
    key = data["api_key"]
    with open(_KEY_CACHE, "w") as fh:
        fh.write(key)
    return key


class Shield:
    """Thin wrapper over POST /v2/scan in enforce mode."""

    def __init__(self, api_key=None):
        self.api_key = api_key or get_api_key()

    def scan(self, content):
        status, data = _post(
            "/v2/scan",
            {"content": content, "content_type": "text", "mode": "enforce"},
            self.api_key,
        )
        if status != 200:
            raise RuntimeError(f"Agent-Shield scan failed: HTTP {status}: {data}")
        return data

    @staticmethod
    def is_blocked(scan_result):
        """Enforce-mode policy: anything not explicitly allowed is blocked."""
        return scan_result.get("action") != "allow" or scan_result.get("verdict") == "malicious"
