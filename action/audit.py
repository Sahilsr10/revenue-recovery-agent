"""Audit trail management — logging and CSV export."""
import csv
import os
from datetime import datetime
from data.models import AuditRecord

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_CSV_PATH = os.path.join(PROJECT_ROOT, "audit_log.csv")

AUDIT_COLUMNS = [
    "audit_id", "timestamp", "event_id", "customer_id", "event_type",
    "root_cause", "risk_level", "decision", "action_taken", "message_sent",
    "attempt_number", "amount", "recovered", "recovered_amount", "outcome",
    "stopping_rule_triggered", "stopping_rule_detail"
]


def export_audit_csv(records: list[AuditRecord], path: str | None = None) -> str:
    """Export audit records to CSV. Returns the output path."""
    output_path = path or AUDIT_CSV_PATH
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_COLUMNS)
        writer.writeheader()
        for record in records:
            row = record.model_dump()
            # Convert enums to strings
            for key in ["event_type", "root_cause", "risk_level", "decision"]:
                if hasattr(row[key], "value"):
                    row[key] = row[key].value
            # Format timestamp
            if isinstance(row["timestamp"], datetime):
                row["timestamp"] = row["timestamp"].isoformat()
            writer.writerow(row)
    return output_path


def print_audit_summary(records: list[AuditRecord]) -> dict:
    """Print and return summary statistics from audit records."""
    total_events = len(records)
    total_at_risk = sum(r.amount for r in records)
    total_recovered = sum(r.recovered_amount for r in records)
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0
    
    stopped_count = sum(1 for r in records if r.stopping_rule_triggered)
    escalated_count = sum(1 for r in records if r.outcome == "escalated")
    recovered_count = sum(1 for r in records if r.recovered)
    
    print("\n" + "=" * 60)
    print("  REVENUE RECOVERY AGENT — BATCH RESULTS")
    print("=" * 60)
    print(f"  Total events processed:     {total_events}")
    print(f"  Revenue at risk:            ₹{total_at_risk:,.0f}")
    print(f"  Revenue recovered:          ₹{total_recovered:,.0f}")
    print(f"  Recovery rate:              {recovery_rate:.1f}%")
    print(f"  Events recovered:           {recovered_count}")
    print(f"  Stopping rules triggered:   {stopped_count}")
    print(f"  Escalated to human:         {escalated_count}")
    print("=" * 60)
    
    # Breakdown by root cause
    from collections import defaultdict
    by_cause = defaultdict(lambda: {"count": 0, "at_risk": 0, "recovered": 0})
    for r in records:
        cause = r.root_cause.value if hasattr(r.root_cause, "value") else r.root_cause
        by_cause[cause]["count"] += 1
        by_cause[cause]["at_risk"] += r.amount
        by_cause[cause]["recovered"] += r.recovered_amount
    
    print("\n  Breakdown by Root Cause:")
    print(f"  {'Root Cause':<30} {'Count':>6} {'At Risk':>12} {'Recovered':>12} {'Rate':>8}")
    print("  " + "-" * 70)
    for cause, stats in sorted(by_cause.items()):
        rate = (stats['recovered'] / stats['at_risk'] * 100) if stats['at_risk'] > 0 else 0
        print(f"  {cause:<30} {stats['count']:>6} ₹{stats['at_risk']:>10,.0f} ₹{stats['recovered']:>10,.0f} {rate:>6.1f}%")
    print()
    
    return {
        "total_events": total_events,
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "recovery_rate": recovery_rate,
        "recovered_count": recovered_count,
        "stopped_count": stopped_count,
        "escalated_count": escalated_count,
    }
