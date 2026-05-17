"""
constants.py — Application-wide constants.

Centralising these values here prevents magic strings from being
scattered across the codebase and makes it easy to extend the system
(e.g. adding a new intent or tool) in one place.
"""

# ── Intent Labels ────────────────────────────────────────────────────────────
# These are the intent classes the LLM is asked to classify user queries into.
INTENT_GREETING = "greeting"
INTENT_BILLING = "billing_issue"
INTENT_TECHNICAL = "technical_issue"
INTENT_RECHARGE = "recharge_issue"
INTENT_FAQ = "faq"
INTENT_COMPLAINT = "complaint"
INTENT_SUBSCRIPTION = "subscription_query"
INTENT_UNKNOWN = "unknown"

# Ordered list used in prompts and validation
ALL_INTENTS = [
    INTENT_GREETING,
    INTENT_BILLING,
    INTENT_TECHNICAL,
    INTENT_RECHARGE,
    INTENT_FAQ,
    INTENT_COMPLAINT,
    INTENT_SUBSCRIPTION,
    INTENT_UNKNOWN,
]

# ── Tool Names ───────────────────────────────────────────────────────────────
TOOL_CRM = "crm_lookup"
TOOL_INTERNET_DIAG = "internet_diagnostic"
TOOL_FAQ = "faq_lookup"
TOOL_NONE = "none"

# Maps intent → preferred tool (used by the routing node)
INTENT_TOOL_MAP: dict[str, str] = {
    INTENT_BILLING: TOOL_CRM,
    INTENT_RECHARGE: TOOL_CRM,
    INTENT_SUBSCRIPTION: TOOL_CRM,
    INTENT_TECHNICAL: TOOL_INTERNET_DIAG,
    INTENT_FAQ: TOOL_FAQ,
    INTENT_COMPLAINT: TOOL_CRM,
    INTENT_GREETING: TOOL_NONE,
    INTENT_UNKNOWN: TOOL_NONE,
}

# ── Graph Node Names ─────────────────────────────────────────────────────────
# Constants for LangGraph node identifiers — avoids typos in wiring.
NODE_INTENT_DETECTION = "intent_detection_node"
NODE_TOOL_ROUTING = "tool_routing_node"
NODE_TOOL_EXECUTION = "tool_execution_node"
NODE_RESPONSE_GENERATION = "response_generation_node"

# ── Fallback / Default Messages ──────────────────────────────────────────────
FALLBACK_RESPONSE = (
    "I'm sorry, I wasn't able to process your request at this time. "
    "Please try again or contact our support team at 1800-XXX-XXXX."
)

GREETING_RESPONSE = (
    "Hello! Welcome to Customer Support. I'm your AI assistant. "
    "How can I help you today?"
)

# ── UI Labels ────────────────────────────────────────────────────────────────
INTENT_DISPLAY_NAMES: dict[str, str] = {
    INTENT_GREETING: "Greeting",
    INTENT_BILLING: "Billing Issue",
    INTENT_TECHNICAL: "Technical Issue",
    INTENT_RECHARGE: "Recharge / Payment",
    INTENT_FAQ: "General FAQ",
    INTENT_COMPLAINT: "Complaint",
    INTENT_SUBSCRIPTION: "Subscription Query",
    INTENT_UNKNOWN: "Unknown",
}

TOOL_DISPLAY_NAMES: dict[str, str] = {
    TOOL_CRM: "CRM Account Lookup",
    TOOL_INTERNET_DIAG: "Internet Diagnostic",
    TOOL_FAQ: "FAQ Knowledge Base",
    TOOL_NONE: "—",
}

# ── Example Queries (used in Streamlit sidebar) ───────────────────────────────
EXAMPLE_QUERIES = [
    "What is my current account balance?",
    "My internet has been slow since yesterday.",
    "I want to upgrade my subscription plan.",
    "How do I recharge my account?",
    "I'm getting call drops every evening.",
    "What are your broadband packages?",
    "How do I reset my router?",
    "I was charged twice this month.",
]
