"""Synthetic batch generator using Faker for the Revenue Recovery Agent."""
import argparse
import csv
import os
import random
from datetime import datetime, timedelta
from faker import Faker
from data.models import EventType, RawEvent
from data.db import get_connection, init_db, insert_raw_events

fake = Faker('en_IN')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, 'events.db')
CSV_PATH = os.path.join(PROJECT_ROOT, 'demo_batch.csv')


def _generate_customers(n=80):
    """Generate a pool of synthetic customers."""
    customers = []
    for _ in range(n):
        customers.append({
            "customer_id": f"cust_{fake.uuid4()[:8]}",
            "customer_name": fake.name(),
            "customer_email": fake.email(),
            "customer_phone": fake.phone_number(),
        })
    return customers


def generate_batch(size: int = 400, seed: int = 42) -> list[RawEvent]:
    """Generate a batch of synthetic revenue-leak events.

    Distribution:
      - 30% checkout_abandoned (split: payment_step / details_step)
      - 25% payment_failed (split: insufficient_funds / bank_issuer_error)
      - 25% subscription_failed (split: expired_card / bank_declined)
      - 20% invoice_overdue (split: no_response / broken_promise_to_pay)

    About 70% are labeled is_recoverable=True (ground truth).
    """
    random.seed(seed)
    Faker.seed(seed)

    customers = _generate_customers(80)
    events: list[RawEvent] = []

    for _ in range(size):
        cust = random.choice(customers)
        rand = random.random()

        amount = round(random.uniform(200, 50000), 2)
        is_recoverable = random.random() < 0.7

        event_type = None
        failure_reason = None
        drop_off_stage = None
        promise_to_pay_date = None
        sub_id = None
        inv_id = None
        plink_id = None

        if rand < 0.30:
            # Checkout abandoned
            event_type = EventType.CHECKOUT_ABANDONED
            drop_off_stage = random.choice(["payment_step", "details_step"])
            plink_id = f"plink_{fake.uuid4()[:8]}"
        elif rand < 0.55:
            # Payment failed
            event_type = EventType.PAYMENT_FAILED
            failure_reason = random.choice([
                "insufficient_funds", "insufficient funds in account",
                "bank_issuer_error", "bank network timeout",
                "issuer declined transaction"
            ])
        elif rand < 0.80:
            # Subscription failed
            event_type = EventType.SUBSCRIPTION_FAILED
            failure_reason = random.choice([
                "expired_card", "card expired",
                "subscription_bank_declined", "bank declined mandate",
                "declined by issuer"
            ])
            amount = round(random.uniform(199, 2999), 2)
            sub_id = f"sub_{fake.uuid4()[:8]}"
        else:
            # Invoice overdue
            event_type = EventType.INVOICE_OVERDUE
            inv_id = f"inv_{fake.uuid4()[:8]}"
            if random.random() < 0.5:
                # Broken promise to pay
                failure_reason = "broken_promise_to_pay"
                days_ago = random.randint(1, 10)
                promise_to_pay_date = datetime.utcnow() - timedelta(days=days_ago)
            else:
                failure_reason = "invoice_no_response"

        event = RawEvent(
            event_type=event_type,
            customer_id=cust["customer_id"],
            customer_email=cust["customer_email"],
            customer_phone=cust["customer_phone"],
            customer_name=cust["customer_name"],
            amount=amount,
            failure_reason=failure_reason,
            subscription_id=sub_id,
            invoice_id=inv_id,
            payment_link_id=plink_id,
            drop_off_stage=drop_off_stage,
            promise_to_pay_date=promise_to_pay_date,
            is_recoverable=is_recoverable,
        )
        events.append(event)

    return events


def save_batch_csv(events: list[RawEvent], path: str | None = None) -> str:
    """Export events to CSV. Returns the output path."""
    output_path = path or CSV_PATH
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if events:
            headers = list(events[0].model_dump().keys())
            writer.writerow(headers)
            for event in events:
                row_data = event.model_dump()
                # Convert enums and datetimes to strings
                cleaned = []
                for v in row_data.values():
                    if hasattr(v, 'value'):
                        cleaned.append(v.value)
                    elif isinstance(v, datetime):
                        cleaned.append(v.isoformat())
                    else:
                        cleaned.append(v)
                writer.writerow(cleaned)
    return output_path


def print_summary(events: list[RawEvent]):
    """Print distribution summary of the generated batch."""
    counts: dict[str, int] = {}
    recoverable = 0
    total_amount = 0.0
    for e in events:
        key = e.event_type.value
        counts[key] = counts.get(key, 0) + 1
        if e.is_recoverable:
            recoverable += 1
        total_amount += e.amount

    print(f"\n  Generated {len(events)} synthetic events")
    print(f"  Total revenue at risk: ₹{total_amount:,.0f}")
    print(f"  Recoverable (ground truth): {recoverable}/{len(events)} "
          f"({recoverable/len(events)*100:.0f}%)")
    print("\n  Distribution:")
    for k, v in sorted(counts.items()):
        print(f"    {k}: {v} ({v/len(events)*100:.0f}%)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic batch")
    parser.add_argument("--size", type=int, default=400, help="Number of events")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    events = generate_batch(size=args.size, seed=args.seed)

    # Save to CSV
    csv_path = save_batch_csv(events)
    print(f"  CSV: {csv_path}")

    # Save to DB
    conn = get_connection(DB_PATH)
    init_db(DB_PATH)
    insert_raw_events(conn, events)
    conn.close()
    print(f"  DB:  {DB_PATH}")

    print_summary(events)


if __name__ == "__main__":
    main()
