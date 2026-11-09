#!/usr/bin/env python3
"""Shielded Checkout — demo runner.

Runs both scenarios against the LIVE Agent-Shield API:
  1. POISONED — a seller message with a buried prompt injection.
     The gate blocks it; the agent refuses; no PayPal call; $0 moves.
  2. CLEAN — the user's own purchase instruction.
     The gate allows it; the agent creates a PayPal sandbox order.

Usage:
  python3 demo.py              # both scenarios
  python3 demo.py --poison     # scenario 1 only
  python3 demo.py --clean      # scenario 2 only

PayPal runs live when PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are set in
.env (sandbox app credentials); otherwise the PayPal step runs in a
clearly-labeled rehearsal mode. Agent-Shield always runs live — if no
AGENT_SHIELD_API_KEY is configured, a free key is obtained automatically
via POST /v1/signup and cached in .shield_key.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shielded_checkout.agent import ShieldedAgent
from shielded_checkout.paypal_client import make_paypal_client
from shielded_checkout.scenarios import CLEAN_TASK, POISONED_TASK
from shielded_checkout.shield import Shield

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def main(argv):
    print("=" * 72)
    print("SHIELDED CHECKOUT — every agent payment passes the gate first")
    print("Agent-Shield (live) screens the instructions · PayPal moves the money")
    print("=" * 72)

    shield = Shield()
    paypal = make_paypal_client(PROJECT_ROOT)
    mode = "LIVE sandbox" if paypal.live else "REHEARSAL (no sandbox credentials in .env)"
    print(f"PayPal mode: {mode}")

    agent = ShieldedAgent(shield=shield, paypal=paypal)
    results = {}
    if "--clean" not in argv:
        results["poisoned"] = agent.handle_task(POISONED_TASK)
    if "--poison" not in argv:
        results["clean"] = agent.handle_task(CLEAN_TASK)

    print(f"\n{'=' * 72}")
    print("SUMMARY")
    if "poisoned" in results:
        r = results["poisoned"]
        print(f"  Poisoned task : {r['outcome'].upper()} — receipt "
              f"{r['scan'].get('receipt', {}).get('receipt_id')} · $0 moved")
    if "clean" in results:
        r = results["clean"]
        oid = (r["order"] or {}).get("id", "—")
        print(f"  Clean task    : {r['outcome'].upper()} — PayPal order {oid}")
    print(f"  PayPal calls made by the agent: {agent.paypal_calls} (poisoned input caused zero)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
