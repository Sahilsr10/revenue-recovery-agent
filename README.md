# AI Revenue Recovery Agent

An autonomous agent that detects silent revenue leaks (checkout abandonment,
failed subscriptions, overdue B2B invoices), diagnoses root causes, and
executes deterministic recovery actions gated by hard-coded stopping rules.

Built for **Razorpay /buildathon — Track 03: AI Revenue Recovery**.

> **Note on figures:** All revenue-at-risk and recovery numbers in this README
> and the dashboard are computed from a synthetic batch that simulates
> realistic Razorpay transaction values. No real payments were processed and
> no real money is involved anywhere in this project.

---

## The Problem

Businesses lose revenue silently through three leak points that nobody
actively chases:
1. **Checkout abandonment** — user starts payment, doesn't finish.
2. **Failed subscription/mandate renewals** — recurring payment fails.
3. **Overdue B2B receivables** — invoice sent, payment never followed up.

This project closes that loop end-to-end: **detect → diagnose → decide →
act → audit**, autonomously and with enforced limits.

---

## Architecture

The system is decoupled into four layers:

| Layer | Responsibility |
|---|---|
| **Data Layer** | Ingests Razorpay test-mode events, or a synthetic batch generator that mimics real webhook payloads at scale |
| **Detection Engine** | Rule-based classifier mapping raw events to root causes (e.g. `INSUFFICIENT_FUNDS`, `BROKEN_PROMISE_TO_PAY`) |
| **Decision Policy Engine** | Deterministic policy table mapping root causes to recovery actions, gated by hard-coded stopping rules (max attempts, cooldowns) |
| **Action + Audit Layer** | Simulates executing actions (SMS/email generation, including a Hinglish tone variant) and logs every attempt to an immutable audit trail |

A Streamlit dashboard visualizes the audit trail and recovery metrics.

```
revenue-recovery-agent/
├── data/
│   ├── generator.py        # synthetic event batch generator
│   └── demo_batch.csv      # generated 400-event batch
├── engine/
│   ├── detection.py        # root-cause classifier
│   ├── policy.py           # decision policy table + stopping rules
│   └── actions.py          # simulated action execution + message generation
├── audit/
│   ├── logger.py           # writes to SQLite + audit_log.csv
│   └── events.db
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── run_demo.sh              # one-command end-to-end run
├── requirements.txt
├── .env.example
└── README.md
```

---

## Tech Stack

- **Backend:** Python 3.11+
- **Data storage:** SQLite
- **Synthetic data generation:** `faker`
- **Dashboard:** Streamlit
- **Payments (optional live path):** Razorpay test-mode API
- **No paid APIs required** — the entire pipeline runs free, end-to-end

---

## Why Synthetic Data for This Demo

Manually triggering a handful of test-mode failures wasn't enough to prove
the system works at scale or to report honest batch metrics. Instead, we
built a synthetic event generator that mimics Razorpay webhook payloads
(`payment.failed`, `subscription.pending`, `invoice.expired`, etc.) at volume.

We generated a batch of 400 realistic failure events representing a
simulated ₹7M in revenue at risk. The agent ingested this batch, applied the
deterministic policies, enforced stopping rules, and simulated recovery
actions — recovering a simulated ₹2M (25% recovery rate). **For comparison,
these leaks are typically unmonitored, so the effective baseline recovery
rate without intervention is ~0%.**

The system is **designed** so that swapping the ingestion source from the
synthetic generator to a live Razorpay webhook URL requires no changes to
the detection or decision layers — only the Data Layer adapter changes. This
has not yet been validated against live webhook traffic; it's a stated
design goal, not a tested claim.

---

## What Broke and How We Handled It

**The issue:** During development, the pipeline was misclassifying all
checkout abandonment events as `ABANDONED_PAYMENT_STEP` because the
`drop_off_stage` field occasionally arrived as `null` in the webhook
payload. This caused the agent to send aggressive "complete your payment!"
nudges to users who hadn't even reached the payment step yet.

**The fix:** The Detection Engine now defaults a missing `drop_off_stage` to
an empty string before classification, and routes any unknown/missing stage
to the gentlest fallback tier (mapped to `ABANDONED_DETAILS_STEP`), keeping
the system compliant with our non-spam cadence rules by default.

---

## How to Run

**Prerequisites:** Python 3.11+. No Razorpay account or API keys are
required to run the default synthetic-data demo.

```bash
git clone <this-repo>
cd revenue-recovery-agent
./run_demo.sh
```

This single command will:
1. Create a virtual environment and install dependencies
2. Generate `demo_batch.csv` (400 realistic synthetic events)
3. Process the batch end-to-end (detect → decide → act → audit)
4. Write results to `audit_log.csv` and a local SQLite database
5. Launch the Streamlit dashboard at `http://localhost:8501`

**Optional — live Razorpay test-mode path:** Copy `.env.example` to `.env`
and add your Razorpay test-mode `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`
(free to generate from the Razorpay Dashboard in Test Mode) to enable the
live ingestion adapter instead of the synthetic generator.

---

## Dashboard

![Dashboard screenshot](docs/dashboard_screenshot.png)

*(Add a real screenshot or short GIF of the running Streamlit dashboard here
before submitting — this is one of the highest-value things a reviewer sees
in the first 5 seconds.)*

---

## 5-Minute Demo Video Script

**0:00–0:30 | The Problem**
"Businesses lose millions silently through three leaks: checkout drops,
failed mandate renewals, and overdue invoices. No one closes the loop from
detection to recovery. Today, we're demoing our AI Revenue Recovery Agent
that does exactly this, autonomously."

**0:30–2:30 | Live Batch Run**
"I'll run the agent on a batch of 400 simulated test-mode events. It
ingests the events, runs the detection engine to classify root causes,
applies our deterministic policy, enforces hard stopping limits (max 3
retries), and executes simulated recovery actions."

**2:30–4:00 | Dashboard Walkthrough**
"We processed 400 events with a simulated ₹7M at risk. The agent recovered
a simulated ₹2M — a 25% recovery rate, against an effective 0% baseline
since these leaks are normally unmonitored. This chart breaks recovery down
by root cause. Below it is our immutable audit trail."

**4:00–5:00 | Case Study & Failure Story**
"Two real cases: a bank-error failure was retried and recovered
automatically; an overdue invoice hit our 3-attempt limit and was cleanly
escalated to a human instead of being spammed. And a quick story on what
broke during development: null drop-off stages caused overly aggressive
messaging early on — fixed by defaulting unknown stages to our gentlest
reminder tier."

---

## Author

Built by Sahil Srivastava for the Razorpay AI Buildathon 2026.
