import pytest
from unittest.mock import MagicMock
from data.models import RootCause, ActionType, ClassifiedEvent
from decision.policy import get_action_plan, apply_policy_batch
from decision.stopping_rules import check_stopping_rules, enforce_stopping_rules

class MockEvent:
    def __init__(self, root_cause):
        self.root_cause = root_cause

class MockActionPlan:
    def __init__(self, max_retries=1):
        self.max_retries = max_retries
        self.action_type = None

def test_policy_insufficient_funds():
    event = MagicMock(root_cause=RootCause.INSUFFICIENT_FUNDS)
    plan = get_action_plan(event)
    assert plan.action_type == ActionType.RETRY_PAYMENT
    assert plan.delay_minutes == 4320
    assert plan.max_retries == 2

def test_policy_bank_issuer_error_first_attempt():
    event = MagicMock(root_cause=RootCause.BANK_ISSUER_ERROR)
    plan = get_action_plan(event, attempt_number=1)
    assert plan.delay_minutes == 15

def test_policy_bank_issuer_error_second_attempt():
    event = MagicMock(root_cause=RootCause.BANK_ISSUER_ERROR)
    plan = get_action_plan(event, attempt_number=2)
    assert plan.delay_minutes == 1440

def test_policy_abandoned_payment_step():
    event = MagicMock(root_cause=RootCause.ABANDONED_PAYMENT_STEP)
    plan = get_action_plan(event)
    assert plan.action_type == ActionType.SEND_NUDGE

def test_policy_broken_promise_first_attempt():
    event = MagicMock(root_cause=RootCause.BROKEN_PROMISE_TO_PAY)
    plan = get_action_plan(event, attempt_number=1)
    assert plan.action_type == ActionType.PROMISE_FOLLOWUP

def test_policy_broken_promise_escalate():
    event = MagicMock(root_cause=RootCause.BROKEN_PROMISE_TO_PAY)
    plan = get_action_plan(event, attempt_number=2)
    assert plan.action_type == ActionType.ESCALATE_TO_HUMAN

def test_stopping_rules_global_max():
    event = MagicMock()
    plan = MockActionPlan()
    stop, reason = check_stopping_rules(event, plan, attempt_number=6)
    assert stop is True
    assert reason == "GLOBAL_MAX_ATTEMPTS_EXCEEDED"

def test_stopping_rules_escalation_history():
    event = MagicMock()
    plan = MockActionPlan()
    stop, reason = check_stopping_rules(event, plan, attempt_number=2, escalation_history=True)
    assert stop is True
    assert reason == "AUTO_STOP_AFTER_ESCALATION"

def test_stopping_rules_max_per_issue():
    event = MagicMock()
    plan = MockActionPlan(max_retries=5)
    stop, reason = check_stopping_rules(event, plan, attempt_number=4)
    assert stop is True
    assert reason == "MAX_ATTEMPTS_PER_CUSTOMER_PER_ISSUE_EXCEEDED"

def test_enforce_stopping_rules():
    event = MagicMock()
    plan = MagicMock()
    plan.max_retries = 1
    plan.action_type = ActionType.RETRY_PAYMENT
    
    enforced = enforce_stopping_rules(event, plan, attempt_number=6)
    assert enforced.action_type == ActionType.NO_ACTION
    assert enforced.stopping_rule_applied == "GLOBAL_MAX_ATTEMPTS_EXCEEDED"
