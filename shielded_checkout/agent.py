"""The Shielded Checkout agent.

Policy (the whole point of the project):
  1. EVERY task — trusted or not — is scanned by Agent-Shield BEFORE the
     agent acts on it. Content is data, not instructions, until the gate
     says otherwise.
  2. If the gate blocks (verdict malicious / action != allow), the agent
     refuses to execute anything from that content and shows the signed
     scan receipt as evidence. No PayPal call is made. $0 moves.
  3. Only on an explicit allow does the agent extract the purchase intent
     and create a PayPal order.
"""

import re

from .shield import Shield
from .paypal_client import approve_link


class PurchaseIntent:
    def __init__(self, item, amount, currency="USD", merchant=""):
        self.item = item
        self.amount = amount
        self.currency = currency
        self.merchant = merchant

    def __str__(self):
        m = f" from {self.merchant}" if self.merchant else ""
        return f"{self.item} — {self.currency} {self.amount}{m}"


def extract_purchase_intent(text):
    """Pull (item, amount, merchant) out of a plain-language purchase task.

    Deliberately simple and deterministic: in this design the *scanner* is
    the AI safety layer, and the purchase instruction itself stays
    transparent and auditable — no free-form model improvisation between
    the gate and the money.
    """
    amount_m = re.search(r"\$\s*(\d+(?:\.\d{2})?)", text)
    if not amount_m:
        return None
    amount = f"{float(amount_m.group(1)):.2f}"
    item_m = re.search(r"(?:buy|order|purchase)\s+(?:the\s+|a\s+|an\s+|one\s+)?(.+?)\s+for\s+\$", text, re.I)
    item = item_m.group(1).strip() if item_m else "Item"
    merchant_m = re.search(r"from\s+([A-Z][\w&.' ]+?)(?:\s*[—.,]|$)", text)
    merchant = merchant_m.group(1).strip() if merchant_m else ""
    return PurchaseIntent(item=item, amount=amount, merchant=merchant)


class ShieldedAgent:
    def __init__(self, shield=None, paypal=None, log=print):
        self.shield = shield or Shield()
        self.paypal = paypal
        self.log = log
        self.paypal_calls = 0

    def handle_task(self, task):
        log = self.log
        log(f"\n{'=' * 72}")
        log(task["title"])
        log(f"Source: {task['source']}")
        log(f"{'-' * 72}")
        log("Incoming task text:")
        for line in task["text"].split("\n"):
            log(f"  | {line}")
        log(f"{'-' * 72}")

        # Step 1 — the gate. Nothing is acted on before this scan.
        log("STEP 1 · Scanning the task with Agent-Shield (POST /v2/scan, enforce mode)…")
        result = self.shield.scan(task["text"])
        receipt = result.get("receipt", {})
        findings = result.get("findings", [])
        log(f"  verdict : {result.get('verdict')}   action: {result.get('action')}")
        scores = result.get("scores", {})
        log(f"  scores  : injection={scores.get('prompt_injection')} "
            f"secrets={scores.get('secrets_exposure')} pii={scores.get('pii_disclosure')} "
            f"ssrf={scores.get('ssrf_risk')}")
        for f in findings:
            sig = f.get("detail", {}).get("signal", "")
            log(f"  finding : {f.get('class')} x{f.get('match_count')}" + (f" ({sig})" if sig else ""))
        log(f"  receipt : {receipt.get('receipt_id')}  (HMAC-signed, verifiable)")
        log(f"  verify  : {receipt.get('verify_url', '')[:100]}…")

        # Step 2 — policy enforcement.
        if Shield.is_blocked(result):
            log("\nSTEP 2 · ⛔ BLOCKED BY THE GATE")
            log("  This content tried to instruct the agent. The agent refuses to")
            log("  execute ANY instruction from it — including the purchase it")
            log("  appeared to offer. No PayPal call is made. $0 moves.")
            log(f"  Evidence: signed receipt {receipt.get('receipt_id')}")
            return {"outcome": "blocked", "scan": result, "order": None}

        log("\nSTEP 2 · ✅ Gate allows it — extracting the purchase intent…")
        intent = extract_purchase_intent(task["text"])
        if intent is None:
            log("  No clear purchase (item + price) found. Agent stops and asks the user.")
            return {"outcome": "no_intent", "scan": result, "order": None}
        log(f"  intent  : {intent}")

        # Step 3 — the money, only ever reached on an allow.
        log("\nSTEP 3 · Creating the PayPal order (Orders v2, intent CAPTURE)…")
        if not self.paypal.live:
            log("  ⚠ REHEARSAL MODE: no PayPal sandbox credentials configured,")
            log("    so this step is simulated and clearly labeled. Add sandbox")
            log("    credentials to .env to run it against PayPal for real.")
        self.paypal_calls += 1
        order = self.paypal.create_order(
            item=intent.item, amount=intent.amount,
            currency=intent.currency, merchant=intent.merchant,
        )
        log(f"  order id: {order.get('id')}")
        log(f"  status  : {order.get('status')}")
        link = approve_link(order)
        if link:
            log(f"  approve : {link}")
        log("  The buyer approves in PayPal; the agent never touches credentials.")
        return {"outcome": "ordered", "scan": result, "order": order}
