"""End-to-end pipeline: generate → detect → decide → act → audit."""
import sys
import os
import random

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from data.models import RawEvent, ClassifiedEvent
from data.generate_batch import generate_batch, save_batch_csv
from data.db import init_db, get_connection, insert_raw_events, insert_audit_records
from detection.classifier import classify_batch
from decision.policy import apply_policy_batch
from decision.stopping_rules import enforce_stopping_rules
from action.executor import execute_batch
from action.audit import export_audit_csv, print_audit_summary


def run(batch_size: int = 400, seed: int = 42):
    """Run the full recovery pipeline."""
    random.seed(seed)
    
    print("[1/6] Generating synthetic batch...")
    events = generate_batch(size=batch_size, seed=seed)
    batch_csv = save_batch_csv(events)
    print(f"      Generated {len(events)} events → {batch_csv}")
    
    print("[2/6] Initializing database...")
    db_path = os.path.join(PROJECT_ROOT, "events.db")
    conn = get_connection(db_path)
    init_db(db_path)
    insert_raw_events(conn, events)
    print(f"      Inserted {len(events)} events into {db_path}")
    
    print("[3/6] Running detection engine...")
    classified = classify_batch(events)
    print(f"      Classified {len(classified)} events")
    
    print("[4/6] Applying decision policy + stopping rules...")
    plans = apply_policy_batch(classified)
    # Apply stopping rules
    enforced_plans = []
    for event, plan in zip(classified, plans):
        enforced = enforce_stopping_rules(event, plan, plan.retry_count + 1)
        enforced_plans.append(enforced)
    plans = enforced_plans
    print(f"      Generated {len(plans)} action plans")
    
    print("[5/6] Executing actions (simulated)...")
    # Randomly use Hinglish for ~30% of messages
    audit_records = []
    for event, plan in zip(classified, plans):
        use_hinglish = random.random() < 0.3
        from action.executor import execute_action
        record = execute_action(event, plan, 
                               attempt_number=plan.retry_count + 1,
                               hinglish=use_hinglish)
        audit_records.append(record)
    print(f"      Executed {len(audit_records)} actions")
    
    print("[6/6] Exporting audit trail...")
    audit_path = export_audit_csv(audit_records)
    insert_audit_records(conn, audit_records)
    conn.close()
    print(f"      Exported audit log → {audit_path}")
    
    # Print summary
    summary = print_audit_summary(audit_records)
    
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Revenue Recovery Agent Pipeline")
    parser.add_argument("--size", type=int, default=400, help="Batch size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    run(batch_size=args.size, seed=args.seed)
