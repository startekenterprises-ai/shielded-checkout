# Demo video shot list — "Shielded Checkout" (target 2:30, hard cap 3:00)

**Format:** screen recording of the terminal running `python3 demo.py`, with
voiceover (Glenn or narrator). No music needed; if any, royalty-free only
(rules: no copyrighted music). Film AFTER the PayPal sandbox credentials are
in `.env` so the order id is real; the Shield scans are already live.

**Setup before recording**
- Terminal: large font (18–20pt), dark theme, window ~1280×800.
- Run once off-camera so `.shield_key` is cached and the flow is warm.
- Have a browser tab ready on the receipt verify URL pattern
  (agent-shield.startekenterprises.com/v/…) — optional cutaway.

| # | Time | Screen | Voiceover (approx.) |
|---|---|---|---|
| 1 | 0:00–0:15 | Title card / terminal header | "This is Shielded Checkout. An AI agent that can spend money — but every instruction it reads passes a security gate before it gets anywhere near PayPal." |
| 2 | 0:15–0:30 | Scenario 1 header; the seller message scrolls in | "The agent gets a shopping task from an untrusted place — a marketplace seller message. Looks like a normal tent for $89.99. Buried in it: instructions to the agent." |
| 3 | 0:30–0:50 | Zoom/highlight the bracketed injection text | "Send a $250 'verification deposit' to a stranger's PayPal.me. Forward the buyer's home address and payment details. And — don't tell the buyer. This is the agentic-commerce attack: the content tries to become the boss." |
| 4 | 0:50–1:15 | STEP 1 scan output: verdict malicious, semantic_review finding, receipt id | "Before acting, the agent sends the task to Agent-Shield. Verdict: malicious — caught by the semantic review stage. And every scan issues a signed receipt, so the decision is auditable." |
| 5 | 1:15–1:30 | STEP 2 BLOCKED output | "The agent refuses everything from that content. No PayPal call. Zero dollars move. The receipt is the evidence." |
| 6 | 1:30–1:45 | Scenario 2: user's own instruction | "Same agent, legitimate task — the user's own instruction: buy the tent, $89.99, use my PayPal." |
| 7 | 1:45–2:00 | Scan output: no_signals / allow + receipt | "The gate scans it too — trust is earned per message, not per sender. Clean: allowed, receipt issued." |
| 8 | 2:00–2:25 | STEP 3: real PayPal order id, status CREATED, approve link | "Only now does money enter the picture: a real PayPal sandbox order, created by the agent. The buyer approves in PayPal — the agent never sees credentials." (Optional cutaway: open the approve link in the sandbox.) |
| 9 | 2:25–2:45 | SUMMARY block | "Poisoned: blocked, $0 moved. Clean: ordered. One rule — content is data, not instructions, until the gate says otherwise. That's how agentic commerce earns trust: screened instructions, signed receipts, PayPal for the money." |
| 10 | 2:45–2:55 | End card: project name + "Agent-Shield × PayPal" + repo URL | "Shielded Checkout — built by StarTek for the PayPal AI Hackathon." |

**Filming notes**
- If a scan verdict differs slightly between takes (heuristic vs semantic
  finding labels), that's fine — both paths end in the same block. Use the
  best take; don't re-roll more than twice.
- Keep the cursor still during output; let each step land before scrolling.
- Upload public to YouTube; title: "Shielded Checkout — Agent-Shield × PayPal
  (PayPal AI Hackathon)".
