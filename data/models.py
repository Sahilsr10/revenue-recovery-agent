"""Shared data models for the Revenue Recovery Agent."""
import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class EventType(str, enum.Enum):
    CHECKOUT_ABANDONED = "checkout_abandoned"
    PAYMENT_FAILED = "payment_failed"
    SUBSCRIPTION_FAILED = "subscription_failed"
    INVOICE_OVERDUE = "invoice_overdue"


class RootCause(str, enum.Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    BANK_ISSUER_ERROR = "bank_issuer_error"
    ABANDONED_PAYMENT_STEP = "abandoned_at_payment_step"
    ABANDONED_DETAILS_STEP = "abandoned_at_details_step"
    EXPIRED_CARD = "expired_card"
    SUBSCRIPTION_BANK_DECLINED = "subscription_bank_declined"
    INVOICE_NO_RESPONSE = "invoice_no_response"
    BROKEN_PROMISE_TO_PAY = "broken_promise_to_pay"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, enum.Enum):
    RETRY_PAYMENT = "retry_payment"
    SEND_REMINDER = "send_reminder"
    SEND_NUDGE = "send_nudge"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    PROMISE_FOLLOWUP = "promise_followup"
    NO_ACTION = "no_action"


class RecoveryLane(str, enum.Enum):
    CHECKOUT_RECOVERY = "checkout_recovery"
    SUBSCRIPTION_RECOVERY = "subscription_recovery"
    INVOICE_RECOVERY = "invoice_recovery"


class RawEvent(BaseModel):
    """A raw payment/subscription/invoice event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    customer_id: str
    customer_email: str
    customer_phone: str
    customer_name: str
    amount: float  # in INR
    currency: str = "INR"
    failure_reason: Optional[str] = None
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    payment_link_id: Optional[str] = None
    drop_off_stage: Optional[str] = None  # for checkout abandonment
    promise_to_pay_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_recoverable: bool = True  # ground truth label for metrics


class ClassifiedEvent(BaseModel):
    """Event after detection/classification."""
    event_id: str
    event_type: EventType
    root_cause: RootCause
    risk_level: RiskLevel
    recommended_lane: RecoveryLane
    customer_id: str
    customer_email: str
    customer_phone: str
    customer_name: str
    amount: float
    currency: str = "INR"
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    payment_link_id: Optional[str] = None
    promise_to_pay_date: Optional[datetime] = None
    created_at: datetime
    is_recoverable: bool = True


class ActionPlan(BaseModel):
    """Decision output: what action to take for a classified event."""
    event_id: str
    action_type: ActionType
    delay_minutes: int = 0  # how long to wait before executing
    message_text: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    cooldown_hours: int = 24
    escalation_triggered: bool = False
    stopping_rule_applied: Optional[str] = None


class AuditRecord(BaseModel):
    """One row in the audit trail."""
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_id: str
    customer_id: str
    event_type: EventType
    root_cause: RootCause
    risk_level: RiskLevel
    decision: ActionType
    action_taken: str  # human-readable description
    message_sent: Optional[str] = None
    attempt_number: int = 1
    amount: float = 0.0
    recovered: bool = False
    recovered_amount: float = 0.0
    outcome: str = "pending"
    stopping_rule_triggered: bool = False
    stopping_rule_detail: Optional[str] = None
