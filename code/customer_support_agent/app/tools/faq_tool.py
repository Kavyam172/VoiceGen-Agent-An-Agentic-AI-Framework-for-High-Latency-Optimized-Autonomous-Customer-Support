"""
faq_tool.py — FAQ knowledge-base lookup tool.

Provides instant answers to common support questions without an LLM call.
In a production system this would query a vector database (e.g. Pinecone,
Weaviate) for semantic search over a large FAQ corpus.

For this demo, answers are stored in a simple dict keyed by topic slug,
with basic keyword matching to select the best entry.

The tool is decorated with @tool for LangChain discovery and invocation.
"""

import json

from langchain_core.tools import tool

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── FAQ Knowledge Base ────────────────────────────────────────────────────────
_FAQ_DATABASE: dict[str, dict] = {
    "reset_password": {
        "question": "How do I reset my account password?",
        "answer": (
            "To reset your password: visit our website → click 'Forgot Password' → "
            "enter your registered mobile number → verify via OTP → set a new password. "
            "Alternatively, call 1800-XXX-XXXX for assisted reset."
        ),
        "keywords": ["password", "reset", "forgot", "login", "sign in"],
    },
    "recharge_process": {
        "question": "How do I recharge my account?",
        "answer": (
            "You can recharge via: (1) Our mobile app, (2) Website at www.telecom.example.com/recharge, "
            "(3) Nearest retail outlet, (4) Net banking / UPI. "
            "Recharges are processed instantly during business hours."
        ),
        "keywords": ["recharge", "top up", "topup", "prepaid", "add balance", "payment"],
    },
    "plans_and_pricing": {
        "question": "What broadband / mobile plans do you offer?",
        "answer": (
            "We offer three plan tiers: "
            "Basic (₹299/mo — 10 GB, unlimited calls), "
            "Standard (₹499/mo — 20 GB, unlimited calls + 100 SMS), "
            "Unlimited Pro 5G (₹999/mo — 100 GB 5G data + unlimited everything). "
            "Visit www.telecom.example.com/plans for the latest offers."
        ),
        "keywords": ["plan", "plans", "price", "pricing", "package", "offer", "5g", "broadband", "subscription"],
    },
    "router_setup": {
        "question": "How do I set up or reset my router?",
        "answer": (
            "To reset your router: press and hold the RESET button on the back for 10 seconds. "
            "Default WiFi credentials are printed on the router label. "
            "For full setup, download our Router Setup Guide from the support portal or call technical support."
        ),
        "keywords": ["router", "wifi", "wi-fi", "setup", "configure", "reset router", "modem"],
    },
    "helpline": {
        "question": "What is the customer support helpline number?",
        "answer": (
            "Our 24×7 customer support helpline: 1800-XXX-XXXX (toll-free). "
            "Email: support@telecom.example.com. "
            "Live chat available on our website from 8 AM – 10 PM IST."
        ),
        "keywords": ["helpline", "contact", "number", "call", "support number", "phone", "email"],
    },
    "data_rollover": {
        "question": "Does unused data roll over to next month?",
        "answer": (
            "Yes! On Standard and Unlimited Pro 5G plans, up to 10 GB of unused data rolls over "
            "to the following month. Basic plan does not include data rollover."
        ),
        "keywords": ["rollover", "roll over", "unused data", "carry forward", "leftover data"],
    },
    "bill_due_date": {
        "question": "When is my bill due?",
        "answer": (
            "Your bill is generated on the 1st of each month and is due by the 15th. "
            "You can view your current bill and due date by logging in to the app or website. "
            "Auto-pay is available to avoid late fees."
        ),
        "keywords": ["bill", "due date", "due", "invoice", "payment date", "billing cycle"],
    },
    "cancellation": {
        "question": "How do I cancel my subscription?",
        "answer": (
            "To cancel your subscription, please call 1800-XXX-XXXX or visit a service centre. "
            "Note: cancellations require 30-day advance notice. "
            "Your service will remain active until the end of the current billing period."
        ),
        "keywords": ["cancel", "cancellation", "terminate", "stop service", "deactivate"],
    },
}

_FALLBACK_FAQ = {
    "question": "General FAQ",
    "answer": (
        "I can help with password resets, recharges, plan details, router setup, "
        "billing queries, and more. Please call 1800-XXX-XXXX for queries not covered here."
    ),
}


@tool
def faq_lookup(query: str) -> str:
    """
    Search the FAQ knowledge base and return the best-matching answer.

    Uses keyword matching to find the most relevant FAQ entry.
    Returns the question and answer as a JSON string.

    Parameters
    ----------
    query : str
        The customer's question or topic to look up.
    """
    logger.info("FAQ lookup called with query: %r", query[:80])

    query_lower = query.lower()

    best_match: dict | None = None
    best_score = 0

    for topic, entry in _FAQ_DATABASE.items():
        score = sum(1 for kw in entry["keywords"] if kw in query_lower)
        if score > best_score:
            best_score = score
            best_match = entry

    chosen = best_match if best_score > 0 else _FALLBACK_FAQ

    result = {
        "status": "success",
        "matched_score": best_score,
        "faq": {
            "question": chosen["question"],
            "answer": chosen["answer"],
        },
    }

    logger.debug("FAQ matched with score %d: %s", best_score, chosen["question"])
    return json.dumps(result, indent=2)
