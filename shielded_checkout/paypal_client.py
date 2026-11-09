"""PayPal Orders v2 client (sandbox) + a clearly-labeled rehearsal stand-in.

Live client implements the documented PayPal REST flow:
  1. POST https://api-m.sandbox.paypal.com/v1/oauth2/token
       (HTTP Basic: client_id:client_secret, grant_type=client_credentials)
  2. POST https://api-m.sandbox.paypal.com/v2/checkout/orders
       {"intent": "CAPTURE", "purchase_units": [{"amount": {...}, ...}]}
  3. GET  https://api-m.sandbox.paypal.com/v2/checkout/orders/{id}

Credentials come from the environment or a local .env file:
  PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET  (sandbox app credentials)

If no credentials are configured, RehearsalPayPalClient is used instead: it
has the same interface and prints an unmistakable REHEARSAL banner, so the
full agent flow can be filmed end-to-end before the sandbox app exists.
It never pretends a real PayPal call happened.
"""

import base64
import json
import os
import urllib.error
import urllib.request
import uuid

SANDBOX_BASE = "https://api-m.sandbox.paypal.com"
_UA = "ShieldedCheckout/1.0 (PayPal AI Hackathon demo)"


def load_dotenv(path):
    """Minimal .env loader (no third-party dependency)."""
    if not os.path.exists(path):
        return
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class PayPalError(RuntimeError):
    pass


class PayPalClient:
    """Real PayPal sandbox client (Orders v2, intent CAPTURE)."""

    live = True

    def __init__(self, client_id, client_secret, base=SANDBOX_BASE):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base = base
        self._token = None

    def _request(self, method, path, body=None, basic_auth=False,
                 content_type="application/json"):
        headers = {"User-Agent": _UA, "Content-Type": content_type}
        if basic_auth:
            raw = f"{self.client_id}:{self.client_secret}".encode()
            headers["Authorization"] = "Basic " + base64.b64encode(raw).decode()
        else:
            headers["Authorization"] = "Bearer " + self.access_token()
        data = None
        if body is not None:
            data = body if isinstance(body, (bytes, str)) else json.dumps(body)
            if isinstance(data, str):
                data = data.encode()
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_body = resp.read().decode()
                return resp.status, json.loads(raw_body) if raw_body else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode()
            raise PayPalError(f"PayPal {method} {path} -> HTTP {e.code}: {detail[:400]}")

    def access_token(self):
        if self._token:
            return self._token
        status, data = self._request(
            "POST", "/v1/oauth2/token",
            body="grant_type=client_credentials", basic_auth=True,
            content_type="application/x-www-form-urlencoded",
        )
        if status != 200 or "access_token" not in data:
            raise PayPalError(f"OAuth token request failed: HTTP {status}: {data}")
        self._token = data["access_token"]
        return self._token

    def create_order(self, item, amount, currency="USD", merchant=""):
        body = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": "shielded-checkout-" + uuid.uuid4().hex[:8],
                "description": (item + (f" — {merchant}" if merchant else ""))[:127],
                "amount": {"currency_code": currency, "value": amount},
            }],
        }
        status, data = self._request("POST", "/v2/checkout/orders", body=body)
        if status not in (200, 201):
            raise PayPalError(f"Create order failed: HTTP {status}: {data}")
        return data

    def get_order(self, order_id):
        status, data = self._request("GET", f"/v2/checkout/orders/{order_id}")
        if status != 200:
            raise PayPalError(f"Get order failed: HTTP {status}: {data}")
        return data


class RehearsalPayPalClient:
    """Offline stand-in with the same interface. Used ONLY when no sandbox
    credentials are configured, and always labeled as a rehearsal."""

    live = False

    def create_order(self, item, amount, currency="USD", merchant=""):
        fake_id = "REHEARSAL-" + uuid.uuid4().hex[:10].upper()
        return {
            "id": fake_id,
            "status": "CREATED (REHEARSAL — no PayPal call was made)",
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": item,
                "amount": {"currency_code": currency, "value": amount},
            }],
            "links": [{
                "rel": "payer-action",
                "href": "https://www.sandbox.paypal.com/checkoutnow?token=" + fake_id,
            }],
        }

    def get_order(self, order_id):
        return {"id": order_id, "status": "CREATED (REHEARSAL)"}


def make_paypal_client(project_root):
    """Live client when sandbox credentials exist, rehearsal client otherwise."""
    load_dotenv(os.path.join(project_root, ".env"))
    cid = os.environ.get("PAYPAL_CLIENT_ID", "").strip()
    secret = os.environ.get("PAYPAL_CLIENT_SECRET", "").strip()
    if cid and secret:
        return PayPalClient(cid, secret)
    return RehearsalPayPalClient()


def approve_link(order):
    for link in order.get("links", []):
        if link.get("rel") in ("payer-action", "approve"):
            return link.get("href")
    return None
