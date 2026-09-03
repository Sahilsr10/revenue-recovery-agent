"""Recovery message templates with Hinglish tone option."""
from data.models import RootCause, ActionType

# Standard English templates
ENGLISH_TEMPLATES = {
    (RootCause.INSUFFICIENT_FUNDS, ActionType.RETRY_PAYMENT): (
        "Hi {name}, your payment of ₹{amount} could not be processed due to "
        "insufficient funds. We'll retry in a few days. Please ensure your "
        "account has adequate balance. Need help? Reply to this message."
    ),
    (RootCause.BANK_ISSUER_ERROR, ActionType.RETRY_PAYMENT): (
        "Hi {name}, your payment of ₹{amount} failed due to a temporary bank "
        "issue. We're retrying automatically — no action needed from you. "
        "If the issue persists, try a different payment method."
    ),
    (RootCause.ABANDONED_PAYMENT_STEP, ActionType.SEND_NUDGE): (
        "Hi {name}, you were just a step away from completing your ₹{amount} "
        "purchase! Your cart is still saved. Complete your order here: {link}"
    ),
    (RootCause.ABANDONED_DETAILS_STEP, ActionType.SEND_REMINDER): (
        "Hi {name}, looks like you started filling in your details for a "
        "₹{amount} order. Need help completing it? We're here for you."
    ),
    (RootCause.EXPIRED_CARD, ActionType.SEND_REMINDER): (
        "Hi {name}, your card on file has expired. Please update your payment "
        "method to continue your ₹{amount}/month subscription without "
        "interruption. Update here: {link}"
    ),
    (RootCause.SUBSCRIPTION_BANK_DECLINED, ActionType.RETRY_PAYMENT): (
        "Hi {name}, your subscription renewal of ₹{amount} was declined by "
        "your bank. We'll retry shortly. If the issue continues, please "
        "contact your bank or try a different card."
    ),
    (RootCause.INVOICE_NO_RESPONSE, ActionType.SEND_REMINDER): (
        "Hi {name}, a friendly reminder that your invoice of ₹{amount} "
        "is pending. Please process the payment at your earliest convenience. "
        "Payment link: {link}"
    ),
    (RootCause.BROKEN_PROMISE_TO_PAY, ActionType.PROMISE_FOLLOWUP): (
        "Hi {name}, we noticed the payment of ₹{amount} that was expected by "
        "{promise_date} hasn't been received yet. Could you provide an update? "
        "We'd like to help resolve this."
    ),
}

# Hinglish templates
HINGLISH_TEMPLATES = {
    (RootCause.INSUFFICIENT_FUNDS, ActionType.RETRY_PAYMENT): (
        "Hi {name}! Aapka ₹{amount} ka payment process nahi ho paya — account "
        "mein balance check kar lijiye. Hum kuch dinon mein retry karenge. "
        "Koi help chahiye? Reply karein!"
    ),
    (RootCause.BANK_ISSUER_ERROR, ActionType.RETRY_PAYMENT): (
        "Hi {name}! ₹{amount} ka payment bank ki wajah se fail ho gaya. "
        "Tension mat lijiye, hum automatically retry kar rahe hain. Agar "
        "problem continue ho, toh dusra payment method try karein."
    ),
    (RootCause.ABANDONED_PAYMENT_STEP, ActionType.SEND_NUDGE): (
        "Hi {name}! Aap ₹{amount} ki purchase se bas ek step door the! "
        "Cart abhi bhi saved hai — yahan se complete karein: {link}"
    ),
    (RootCause.ABANDONED_DETAILS_STEP, ActionType.SEND_REMINDER): (
        "Hi {name}, lagta hai aapne ₹{amount} ke order ke liye details "
        "bharna shuru kiya tha. Koi help chahiye? Hum yahan hain!"
    ),
    (RootCause.EXPIRED_CARD, ActionType.SEND_REMINDER): (
        "Hi {name}! Aapka card expire ho gaya hai. Apna payment method "
        "update karein taaki ₹{amount}/month subscription smoothly chalta "
        "rahe. Update karein: {link}"
    ),
    (RootCause.SUBSCRIPTION_BANK_DECLINED, ActionType.RETRY_PAYMENT): (
        "Hi {name}! ₹{amount} ka subscription renewal bank ne decline kar "
        "diya. Hum jaldi retry karenge. Problem continue ho toh bank se "
        "contact karein ya dusra card try karein."
    ),
    (RootCause.INVOICE_NO_RESPONSE, ActionType.SEND_REMINDER): (
        "Hi {name}! Yaad dila dein — ₹{amount} ka invoice abhi pending hai. "
        "Jaldi se jaldi payment process kar dijiye. Link: {link}"
    ),
    (RootCause.BROKEN_PROMISE_TO_PAY, ActionType.PROMISE_FOLLOWUP): (
        "Hi {name}, ₹{amount} ka payment jo {promise_date} tak expected tha, "
        "abhi tak receive nahi hua. Kya aap update de sakte hain? Hum help "
        "karna chahte hain."
    ),
}

# Escalation templates (always English, formal)
ESCALATION_TEMPLATE = (
    "[INTERNAL — ESCALATE TO HUMAN AGENT] Customer {name} (ID: {customer_id}) "
    "has an unresolved payment of ₹{amount}. Root cause: {root_cause}. "
    "Automated recovery exhausted after {attempts} attempts. "
    "Manual intervention required."
)


def get_message(root_cause: RootCause, action_type: ActionType, 
                hinglish: bool = False, **kwargs) -> str:
    """Generate a recovery message from templates."""
    templates = HINGLISH_TEMPLATES if hinglish else ENGLISH_TEMPLATES
    key = (root_cause, action_type)
    
    if action_type == ActionType.ESCALATE_TO_HUMAN:
        template = ESCALATION_TEMPLATE
    elif key in templates:
        template = templates[key]
    else:
        template = f"Hi {{name}}, regarding your payment of ₹{{amount}} — please contact support."
    
    # Provide defaults for optional format keys
    defaults = {"link": "https://rzp.io/example", "promise_date": "N/A", 
                "customer_id": "N/A", "root_cause": str(root_cause.value),
                "attempts": 0}
    defaults.update(kwargs)
    
    try:
        return template.format(**defaults)
    except KeyError:
        return template  # Return raw template if formatting fails
