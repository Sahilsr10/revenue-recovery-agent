from data.models import ClassifiedEvent, ActionPlan, ActionType, RootCause

# Hard-coded stopping rules
MAX_ATTEMPTS_PER_CUSTOMER_PER_ISSUE = 3
AUTO_STOP_AFTER_ESCALATION = True
MAX_DAILY_CONTACTS_PER_CUSTOMER = 2
GLOBAL_MAX_ATTEMPTS = 5

COOLDOWN_WINDOW_HOURS = {
    RootCause.INSUFFICIENT_FUNDS: 72,
    RootCause.BANK_ISSUER_ERROR: 24,
    RootCause.ABANDONED_PAYMENT_STEP: 48,
    RootCause.ABANDONED_DETAILS_STEP: 48,
    RootCause.EXPIRED_CARD: 72,
    RootCause.SUBSCRIPTION_BANK_DECLINED: 24,
    RootCause.INVOICE_NO_RESPONSE: 168,
    RootCause.BROKEN_PROMISE_TO_PAY: 48,
}

def check_stopping_rules(event: ClassifiedEvent, action_plan: ActionPlan, attempt_number: int, escalation_history: bool = False) -> tuple[bool, str | None]:
    """Checks stopping rules and returns (should_stop, reason)."""
    
    if attempt_number > GLOBAL_MAX_ATTEMPTS:
        return True, "GLOBAL_MAX_ATTEMPTS_EXCEEDED"
        
    if escalation_history and AUTO_STOP_AFTER_ESCALATION:
        return True, "AUTO_STOP_AFTER_ESCALATION"
        
    if attempt_number > MAX_ATTEMPTS_PER_CUSTOMER_PER_ISSUE:
        return True, "MAX_ATTEMPTS_PER_CUSTOMER_PER_ISSUE_EXCEEDED"
        
    if attempt_number > getattr(action_plan, 'max_retries', 0) + 1:
        return True, "MAX_RETRIES_EXCEEDED"
        
    return False, None

def enforce_stopping_rules(event: ClassifiedEvent, action_plan: ActionPlan, attempt_number: int, escalation_history: bool = False) -> ActionPlan:
    """Enforces stopping rules by mutating the action plan to NO_ACTION if needed."""
    should_stop, reason = check_stopping_rules(event, action_plan, attempt_number, escalation_history)
    
    if should_stop:
        action_plan.action_type = ActionType.NO_ACTION
        if hasattr(action_plan, "stopping_rule_applied"):
            action_plan.stopping_rule_applied = reason
        else:
            setattr(action_plan, "stopping_rule_applied", reason)
            
    return action_plan
