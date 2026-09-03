"""Deterministic decision policy table — maps (root_cause, attempt) → action plan."""
from data.models import (
    RootCause, ActionType, ActionPlan, ClassifiedEvent,
)


def get_action_plan(event: ClassifiedEvent, attempt_number: int = 1) -> ActionPlan:
    """Returns the action plan for a classified event based on deterministic policy.

    Policy rules (fully explainable, no black box):
      INSUFFICIENT_FUNDS      → retry in 3 days (payday-aware), max 2 retries
      BANK_ISSUER_ERROR       → retry in 15 min then 24 h, max 2 retries
      ABANDONED_PAYMENT_STEP  → immediate nudge, max 2
      ABANDONED_DETAILS_STEP  → gentle reminder in 2 h, max 1
      EXPIRED_CARD            → reminder to update card, max 1
      SUBSCRIPTION_BANK_DECLINED → retry in 15 min, max 2
      INVOICE_NO_RESPONSE     → Day 1 friendly, Day 7 firm, Day 15 escalate
      BROKEN_PROMISE_TO_PAY   → one follow-up, then escalate
    """
    rc = event.root_cause

    if rc == RootCause.INSUFFICIENT_FUNDS:
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.RETRY_PAYMENT,
            delay_minutes=4320,  # 3 days
            max_retries=2,
            cooldown_hours=72,
        )

    if rc == RootCause.BANK_ISSUER_ERROR:
        delay = 15 if attempt_number == 1 else 1440
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.RETRY_PAYMENT,
            delay_minutes=delay,
            max_retries=2,
            cooldown_hours=24,
        )

    if rc == RootCause.ABANDONED_PAYMENT_STEP:
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.SEND_NUDGE,
            delay_minutes=0,
            max_retries=2,
            cooldown_hours=48,
        )

    if rc == RootCause.ABANDONED_DETAILS_STEP:
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.SEND_REMINDER,
            delay_minutes=120,
            max_retries=1,
            cooldown_hours=48,
        )

    if rc == RootCause.EXPIRED_CARD:
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.SEND_REMINDER,
            delay_minutes=0,
            max_retries=1,
            cooldown_hours=72,
        )

    if rc == RootCause.SUBSCRIPTION_BANK_DECLINED:
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.RETRY_PAYMENT,
            delay_minutes=15,
            max_retries=2,
            cooldown_hours=24,
        )

    if rc == RootCause.INVOICE_NO_RESPONSE:
        if attempt_number == 1:
            action_type = ActionType.SEND_REMINDER
            delay = 0
        elif attempt_number == 2:
            action_type = ActionType.SEND_REMINDER
            delay = 1440 * 7   # Day 7 — firm
        else:
            action_type = ActionType.ESCALATE_TO_HUMAN
            delay = 1440 * 15  # Day 15 — escalate
        return ActionPlan(
            event_id=event.event_id,
            action_type=action_type,
            delay_minutes=delay,
            max_retries=3,
            cooldown_hours=168,
        )

    if rc == RootCause.BROKEN_PROMISE_TO_PAY:
        if attempt_number == 1:
            return ActionPlan(
                event_id=event.event_id,
                action_type=ActionType.PROMISE_FOLLOWUP,
                delay_minutes=0,
                max_retries=1,
                cooldown_hours=48,
            )
        return ActionPlan(
            event_id=event.event_id,
            action_type=ActionType.ESCALATE_TO_HUMAN,
            delay_minutes=0,
            max_retries=1,
            cooldown_hours=48,
            escalation_triggered=True,
        )

    # Fallback — should not be reached with valid data
    return ActionPlan(
        event_id=event.event_id,
        action_type=ActionType.NO_ACTION,
        delay_minutes=0,
        max_retries=0,
        cooldown_hours=0,
    )


def apply_policy_batch(events: list[ClassifiedEvent]) -> list[ActionPlan]:
    """Applies the deterministic policy table to a full batch."""
    return [get_action_plan(event) for event in events]
