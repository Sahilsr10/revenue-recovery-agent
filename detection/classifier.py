from datetime import datetime, timezone
from typing import List
from data.models import (
    RawEvent,
    ClassifiedEvent,
    EventType,
    RootCause,
    RiskLevel,
    RecoveryLane,
)

def classify(event: RawEvent) -> ClassifiedEvent:
    root_cause = RootCause.BANK_ISSUER_ERROR
    risk_level = RiskLevel.MEDIUM
    lane = RecoveryLane.CHECKOUT_RECOVERY
    
    if event.event_type == EventType.CHECKOUT_ABANDONED:
        lane = RecoveryLane.CHECKOUT_RECOVERY
        stage = (event.drop_off_stage or "").lower()
        if "payment" in stage:
            root_cause = RootCause.ABANDONED_PAYMENT_STEP
            risk_level = RiskLevel.HIGH
        elif "details" in stage or "address" in stage:
            root_cause = RootCause.ABANDONED_DETAILS_STEP
            risk_level = RiskLevel.MEDIUM
        else:
            root_cause = RootCause.ABANDONED_PAYMENT_STEP
            risk_level = RiskLevel.HIGH
            
    elif event.event_type == EventType.PAYMENT_FAILED:
        lane = RecoveryLane.CHECKOUT_RECOVERY
        reason = (event.failure_reason or "").lower()
        if "insufficient" in reason or "funds" in reason:
            root_cause = RootCause.INSUFFICIENT_FUNDS
            risk_level = RiskLevel.HIGH
        elif "bank" in reason or "issuer" in reason or "network" in reason:
            root_cause = RootCause.BANK_ISSUER_ERROR
            risk_level = RiskLevel.MEDIUM
        else:
            root_cause = RootCause.BANK_ISSUER_ERROR
            risk_level = RiskLevel.MEDIUM
            
    elif event.event_type == EventType.SUBSCRIPTION_FAILED:
        lane = RecoveryLane.SUBSCRIPTION_RECOVERY
        reason = (event.failure_reason or "").lower()
        if "expired" in reason or "card" in reason:
            root_cause = RootCause.EXPIRED_CARD
            risk_level = RiskLevel.CRITICAL
        elif "bank" in reason or "declined" in reason:
            root_cause = RootCause.SUBSCRIPTION_BANK_DECLINED
            risk_level = RiskLevel.HIGH
        else:
            root_cause = RootCause.SUBSCRIPTION_BANK_DECLINED
            risk_level = RiskLevel.HIGH
            
    elif event.event_type == EventType.INVOICE_OVERDUE:
        lane = RecoveryLane.INVOICE_RECOVERY
        now = datetime.now(timezone.utc)
        ptp = event.promise_to_pay_date
        # Assume ptp is aware or naive, handle naive as utc
        if ptp is not None:
            if ptp.tzinfo is None:
                ptp = ptp.replace(tzinfo=timezone.utc)
            if ptp < now:
                root_cause = RootCause.BROKEN_PROMISE_TO_PAY
                risk_level = RiskLevel.CRITICAL
            else:
                root_cause = RootCause.INVOICE_NO_RESPONSE
                risk_level = RiskLevel.HIGH
        else:
            root_cause = RootCause.INVOICE_NO_RESPONSE
            risk_level = RiskLevel.HIGH

    return ClassifiedEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        root_cause=root_cause,
        risk_level=risk_level,
        recommended_lane=lane,
        customer_id=event.customer_id,
        customer_email=event.customer_email,
        customer_phone=event.customer_phone,
        customer_name=event.customer_name,
        amount=event.amount,
        currency=event.currency,
        subscription_id=event.subscription_id,
        invoice_id=event.invoice_id,
        payment_link_id=event.payment_link_id,
        promise_to_pay_date=event.promise_to_pay_date,
        created_at=event.created_at,
        is_recoverable=event.is_recoverable,
    )

def classify_batch(events: List[RawEvent]) -> List[ClassifiedEvent]:
    return [classify(event) for event in events]
