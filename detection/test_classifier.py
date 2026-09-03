import sys
import os
from datetime import datetime, timezone, timedelta
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.models import RawEvent, EventType, RootCause, RiskLevel, RecoveryLane
from detection.classifier import classify, classify_batch

def create_base_event(event_type: EventType) -> RawEvent:
    return RawEvent(
        event_id="evt_123",
        event_type=event_type,
        customer_id="cust_123",
        customer_email="test@example.com",
        customer_phone="1234567890",
        customer_name="Test User",
        amount=100.0,
        created_at=datetime.now(timezone.utc)
    )

def test_checkout_abandoned_payment_step():
    event = create_base_event(EventType.CHECKOUT_ABANDONED)
    event.drop_off_stage = "in payment"
    classified = classify(event)
    assert classified.root_cause == RootCause.ABANDONED_PAYMENT_STEP
    assert classified.risk_level == RiskLevel.HIGH
    assert classified.recommended_lane == RecoveryLane.CHECKOUT_RECOVERY

def test_checkout_abandoned_details_step():
    event = create_base_event(EventType.CHECKOUT_ABANDONED)
    event.drop_off_stage = "address entry"
    classified = classify(event)
    assert classified.root_cause == RootCause.ABANDONED_DETAILS_STEP
    assert classified.risk_level == RiskLevel.MEDIUM

def test_checkout_abandoned_default():
    event = create_base_event(EventType.CHECKOUT_ABANDONED)
    event.drop_off_stage = None
    classified = classify(event)
    assert classified.root_cause == RootCause.ABANDONED_PAYMENT_STEP
    assert classified.risk_level == RiskLevel.HIGH

def test_payment_failed_insufficient_funds():
    event = create_base_event(EventType.PAYMENT_FAILED)
    event.failure_reason = "Insufficient funds"
    classified = classify(event)
    assert classified.root_cause == RootCause.INSUFFICIENT_FUNDS
    assert classified.risk_level == RiskLevel.HIGH

def test_payment_failed_bank_error():
    event = create_base_event(EventType.PAYMENT_FAILED)
    event.failure_reason = "Bank network down"
    classified = classify(event)
    assert classified.root_cause == RootCause.BANK_ISSUER_ERROR
    assert classified.risk_level == RiskLevel.MEDIUM

def test_subscription_failed_expired_card():
    event = create_base_event(EventType.SUBSCRIPTION_FAILED)
    event.failure_reason = "card has expired"
    classified = classify(event)
    assert classified.root_cause == RootCause.EXPIRED_CARD
    assert classified.risk_level == RiskLevel.CRITICAL
    assert classified.recommended_lane == RecoveryLane.SUBSCRIPTION_RECOVERY

def test_subscription_failed_default():
    event = create_base_event(EventType.SUBSCRIPTION_FAILED)
    event.failure_reason = None
    classified = classify(event)
    assert classified.root_cause == RootCause.SUBSCRIPTION_BANK_DECLINED
    assert classified.risk_level == RiskLevel.HIGH

def test_invoice_overdue_no_response():
    event = create_base_event(EventType.INVOICE_OVERDUE)
    classified = classify(event)
    assert classified.root_cause == RootCause.INVOICE_NO_RESPONSE
    assert classified.risk_level == RiskLevel.HIGH
    assert classified.recommended_lane == RecoveryLane.INVOICE_RECOVERY

def test_invoice_overdue_broken_promise():
    event = create_base_event(EventType.INVOICE_OVERDUE)
    event.promise_to_pay_date = datetime.now(timezone.utc) - timedelta(days=1)
    classified = classify(event)
    assert classified.root_cause == RootCause.BROKEN_PROMISE_TO_PAY
    assert classified.risk_level == RiskLevel.CRITICAL

def test_classify_batch():
    e1 = create_base_event(EventType.CHECKOUT_ABANDONED)
    e2 = create_base_event(EventType.INVOICE_OVERDUE)
    classified_list = classify_batch([e1, e2])
    assert len(classified_list) == 2
    assert classified_list[0].root_cause == RootCause.ABANDONED_PAYMENT_STEP
    assert classified_list[1].root_cause == RootCause.INVOICE_NO_RESPONSE
