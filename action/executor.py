"""Simulated action executor — logs what would happen in production."""
import random
from datetime import datetime
from data.models import (
    ActionType, ActionPlan, ClassifiedEvent, AuditRecord, RootCause
)
from action.templates import get_message


def execute_action(event: ClassifiedEvent, plan: ActionPlan, 
                   attempt_number: int = 1, hinglish: bool = False) -> AuditRecord:
    """Execute a single recovery action (simulated) and return an audit record."""
    
    # Generate message text
    message_text = None
    if plan.action_type in (ActionType.SEND_REMINDER, ActionType.SEND_NUDGE, 
                            ActionType.PROMISE_FOLLOWUP, ActionType.ESCALATE_TO_HUMAN):
        message_text = get_message(
            root_cause=event.root_cause,
            action_type=plan.action_type,
            hinglish=hinglish,
            name=event.customer_name,
            amount=f"{event.amount:,.0f}",
            customer_id=event.customer_id,
            attempts=attempt_number,
            promise_date=event.promise_to_pay_date.strftime("%d %b %Y") if event.promise_to_pay_date else "N/A"
        )
    
    # Simulate outcome
    # Recovery probability depends on root cause and attempt number
    recovery_prob = _get_recovery_probability(event.root_cause, attempt_number)
    is_recovered = event.is_recoverable and (random.random() < recovery_prob)
    recovered_amount = event.amount if is_recovered else 0.0
    
    # Build action description
    if plan.action_type == ActionType.NO_ACTION:
        action_desc = f"No action taken — stopping rule: {plan.stopping_rule_applied}"
    elif plan.action_type == ActionType.RETRY_PAYMENT:
        action_desc = f"[SIMULATED] Retry payment of ₹{event.amount:,.0f} after {plan.delay_minutes}min delay"
        if message_text is None:
            message_text = get_message(
                root_cause=event.root_cause,
                action_type=plan.action_type,
                hinglish=hinglish,
                name=event.customer_name,
                amount=f"{event.amount:,.0f}"
            )
    elif plan.action_type == ActionType.ESCALATE_TO_HUMAN:
        action_desc = f"[ESCALATED] Manual review needed for ₹{event.amount:,.0f}"
        is_recovered = False  # Escalation doesn't count as immediate recovery
        recovered_amount = 0.0
    else:
        channel = "SMS/Email"
        action_desc = f"[SIMULATED] Send {plan.action_type.value} via {channel}"
    
    outcome = "recovered" if is_recovered else "pending"
    if plan.action_type == ActionType.NO_ACTION:
        outcome = "stopped"
    elif plan.action_type == ActionType.ESCALATE_TO_HUMAN:
        outcome = "escalated"
    
    return AuditRecord(
        event_id=event.event_id,
        customer_id=event.customer_id,
        event_type=event.event_type,
        root_cause=event.root_cause,
        risk_level=event.risk_level,
        decision=plan.action_type,
        action_taken=action_desc,
        message_sent=message_text,
        attempt_number=attempt_number,
        amount=event.amount,
        recovered=is_recovered,
        recovered_amount=recovered_amount,
        outcome=outcome,
        stopping_rule_triggered=plan.stopping_rule_applied is not None,
        stopping_rule_detail=plan.stopping_rule_applied
    )


def _get_recovery_probability(root_cause: RootCause, attempt: int) -> float:
    """Realistic recovery probability by root cause and attempt number."""
    base_probs = {
        RootCause.INSUFFICIENT_FUNDS: 0.35,
        RootCause.BANK_ISSUER_ERROR: 0.60,
        RootCause.ABANDONED_PAYMENT_STEP: 0.25,
        RootCause.ABANDONED_DETAILS_STEP: 0.15,
        RootCause.EXPIRED_CARD: 0.20,
        RootCause.SUBSCRIPTION_BANK_DECLINED: 0.45,
        RootCause.INVOICE_NO_RESPONSE: 0.30,
        RootCause.BROKEN_PROMISE_TO_PAY: 0.40,
    }
    base = base_probs.get(root_cause, 0.25)
    # Diminishing returns per attempt
    return base * (0.7 ** (attempt - 1))


def execute_batch(events: list[ClassifiedEvent], plans: list[ActionPlan],
                  hinglish: bool = False) -> list[AuditRecord]:
    """Execute actions for a full batch and return audit records."""
    records = []
    for event, plan in zip(events, plans):
        record = execute_action(event, plan, 
                               attempt_number=plan.retry_count + 1,
                               hinglish=hinglish)
        records.append(record)
    return records
