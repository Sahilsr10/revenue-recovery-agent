import os
import sqlite3
from data.models import RawEvent, ClassifiedEvent, AuditRecord

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'events.db')

def get_connection(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    cur = conn.cursor()
    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS raw_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT,
        customer_id TEXT,
        customer_email TEXT,
        customer_phone TEXT,
        customer_name TEXT,
        amount REAL,
        currency TEXT,
        failure_reason TEXT,
        subscription_id TEXT,
        invoice_id TEXT,
        payment_link_id TEXT,
        drop_off_stage TEXT,
        promise_to_pay_date TIMESTAMP,
        created_at TIMESTAMP,
        is_recoverable BOOLEAN
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS classified_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT,
        root_cause TEXT,
        risk_level TEXT,
        recommended_lane TEXT,
        customer_id TEXT,
        customer_email TEXT,
        customer_phone TEXT,
        customer_name TEXT,
        amount REAL,
        currency TEXT,
        subscription_id TEXT,
        invoice_id TEXT,
        payment_link_id TEXT,
        promise_to_pay_date TIMESTAMP,
        created_at TIMESTAMP,
        is_recoverable BOOLEAN
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS action_plans (
        event_id TEXT PRIMARY KEY,
        action_type TEXT,
        delay_minutes INTEGER,
        message_text TEXT,
        retry_count INTEGER,
        max_retries INTEGER,
        cooldown_hours INTEGER,
        escalation_triggered BOOLEAN,
        stopping_rule_applied TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        audit_id TEXT PRIMARY KEY,
        timestamp TIMESTAMP,
        event_id TEXT,
        customer_id TEXT,
        event_type TEXT,
        root_cause TEXT,
        risk_level TEXT,
        decision TEXT,
        action_taken TEXT,
        message_sent TEXT,
        attempt_number INTEGER,
        amount REAL,
        recovered BOOLEAN,
        recovered_amount REAL,
        outcome TEXT,
        stopping_rule_triggered BOOLEAN,
        stopping_rule_detail TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_raw_events(conn, events: list[RawEvent]):
    cur = conn.cursor()
    for event in events:
        cur.execute('''
        INSERT OR REPLACE INTO raw_events (
            event_id, event_type, customer_id, customer_email, customer_phone, customer_name,
            amount, currency, failure_reason, subscription_id, invoice_id, payment_link_id,
            drop_off_stage, promise_to_pay_date, created_at, is_recoverable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id, event.event_type.value, event.customer_id, event.customer_email,
            event.customer_phone, event.customer_name, event.amount, event.currency,
            event.failure_reason, event.subscription_id, event.invoice_id, event.payment_link_id,
            event.drop_off_stage, event.promise_to_pay_date.isoformat() if event.promise_to_pay_date else None,
            event.created_at.isoformat(), event.is_recoverable
        ))
    conn.commit()

def get_all_raw_events(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM raw_events")
    return [dict(row) for row in cur.fetchall()]

def insert_classified_events(conn, events: list[ClassifiedEvent]):
    cur = conn.cursor()
    for event in events:
        cur.execute('''
        INSERT OR REPLACE INTO classified_events (
            event_id, event_type, root_cause, risk_level, recommended_lane,
            customer_id, customer_email, customer_phone, customer_name,
            amount, currency, subscription_id, invoice_id, payment_link_id,
            promise_to_pay_date, created_at, is_recoverable
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id, event.event_type.value, event.root_cause.value, event.risk_level.value,
            event.recommended_lane.value, event.customer_id, event.customer_email,
            event.customer_phone, event.customer_name, event.amount, event.currency,
            event.subscription_id, event.invoice_id, event.payment_link_id,
            event.promise_to_pay_date.isoformat() if event.promise_to_pay_date else None,
            event.created_at.isoformat(), event.is_recoverable
        ))
    conn.commit()

def insert_audit_records(conn, records: list[AuditRecord]):
    cur = conn.cursor()
    for rec in records:
        cur.execute('''
        INSERT OR REPLACE INTO audit_log (
            audit_id, timestamp, event_id, customer_id, event_type, root_cause,
            risk_level, decision, action_taken, message_sent, attempt_number,
            amount, recovered, recovered_amount, outcome, stopping_rule_triggered,
            stopping_rule_detail
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec.audit_id, rec.timestamp.isoformat(), rec.event_id, rec.customer_id,
            rec.event_type.value, rec.root_cause.value, rec.risk_level.value,
            rec.decision.value, rec.action_taken, rec.message_sent, rec.attempt_number,
            rec.amount, rec.recovered, rec.recovered_amount, rec.outcome,
            rec.stopping_rule_triggered, rec.stopping_rule_detail
        ))
    conn.commit()

def get_all_audit_records(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_log")
    return [dict(row) for row in cur.fetchall()]

def get_customer_attempt_count(conn, customer_id, event_type) -> int:
    cur = conn.cursor()
    if isinstance(event_type, str):
        evt_val = event_type
    else:
        evt_val = event_type.value
    cur.execute('''
        SELECT COUNT(*) FROM audit_log 
        WHERE customer_id = ? AND event_type = ?
    ''', (customer_id, evt_val))
    return cur.fetchone()[0]
