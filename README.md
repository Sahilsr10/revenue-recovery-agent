# AI Revenue Recovery Agent

An autonomous agent that detects silent revenue leaks (checkout abandonment, failed subscriptions, overdue B2B invoices), diagnoses root causes, and executes deterministic recovery actions gated by hard-coded stopping rules.

Built for **Razorpay /buildathon — Track 03: AI Revenue Recovery**.

## Architecture & Workflow

The system is decoupled into four layers:
1. **Data Layer**: Ingests Razorpay test-mode events (simulated via synthetic batch generator).
2. **Detection Engine**: Rule-based classifier mapping raw events to actionable root causes (e.g. `INSUFFICIENT_FUNDS`, `BROKEN_PROMISE_TO_PAY`).
3. **Decision Policy Engine**: Deterministic policy table mapping root causes to recovery actions, heavily gated by enforced stopping rules (max attempts, cooldowns).
4. **Action + Audit Layer**: Simulates executing the actions (SMS/Email generation in standard and Hinglish tones) and comprehensively logs every attempt to an auditable trail.

A Streamlit dashboard visualizes the audit trail and recovery metrics.

---

## Why Synthetic Data for the Demo?

To prove this system works at scale, clicking "fail payment" manually 3 times in a test sandbox wasn't enough. Instead, we built a synthetic event generator that perfectly mimics Razorpay webhook payloads at scale. 

We generated a batch of 400 realistic failures representing over ₹7 Million at risk. Our agent ingested this batch, applied the deterministic policies, enforced stopping rules, and simulated the recoveries. In production, the ingestion layer simply swaps from our synthetic DB to a live Razorpay Webhook URL, but the core AI detection and decision layers remain entirely unchanged.

---

## What Broke and How We Handled It (Failure Story)

**The Issue**: During initial development, the pipeline was classifying all checkout abandonment drop-offs as `ABANDONED_PAYMENT_STEP` because the `drop_off_stage` field was occasionally arriving as `null` (None) in the webhook payloads. This resulted in the agent sending aggressive "complete your payment!" nudges to users who hadn't even entered their shipping details.

**The Fix**: We updated the `Detection Engine` classifier to handle `None` values gracefully by defaulting the stage string to empty `""` before calling `.lower()`. We then routed unknown or missing drop-off stages to the gentlest fallback tier (which maps to `ABANDONED_DETAILS_STEP`), ensuring compliance with non-spam cadence rules.

---

## 5-Minute Demo Video Script

**0:00 - 0:30 | The Problem**
"Businesses lose millions silently through three leaks: checkout drops, failed mandate renewals, and overdue invoices. No one closes the loop from detection to recovery. Today, we're demoing our AI Revenue Recovery Agent that does exactly this, autonomously."

**0:30 - 2:30 | Live Batch Run**
"I'll run the agent on a batch of 400 simulated test-mode events. Watch the terminal. It ingests the events, runs the detection engine to classify root causes, applies our deterministic policy, enforces hard stopping limits (max 3 retries), and executes simulated recovery actions. Done."

**2:30 - 4:00 | Dashboard Walkthrough**
"Let's look at the Streamlit dashboard. We processed 400 events with over ₹7M at risk. The agent successfully recovered ₹2M — a 25% recovery rate. In the pie chart, you see the breakdown by root cause: bank errors, insufficient funds, broken promises to pay. The table below is our immutable audit trail."

**4:00 - 5:00 | Case Study & Failure Story**
"Here are two real cases. In Case 1, a bank error was retried and recovered automatically. In Case 2, an invoice hit our 3-attempt limit and was cleanly escalated to a human without spamming the customer. Finally, a quick story on what broke: early on, null drop-off stages caused aggressive messaging. We fixed this by defaulting unknown stages to our gentlest reminder tier to ensure compliance. Thank you!"

---

## How to Run

1. Ensure Python 3.11+ is installed.
2. Run the automated demo script from the project root:
```bash
./run_demo.sh
```

This single command will:
- Create a virtual environment and install dependencies
- Generate `demo_batch.csv` (400 realistic events)
- Process the batch end-to-end (detect → decide → act → audit)
- Write the results to `audit_log.csv` and an SQLite database
- Launch the Streamlit dashboard at `http://localhost:8501`
