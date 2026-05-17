"""
prompts.py — All LLM prompt templates for the support assistant.

Centralising prompts here makes it easy to iterate on them without
touching business-logic code.  Each function returns a ready-to-use
string; callers substitute their runtime values via Python f-strings.

Prompt design principles used here:
  • Role + task framing at the top
  • Explicit output format so the LLM response is easy to parse
  • Constrained choices where possible (e.g. intent list)
  • Brief few-shot examples for harder classification tasks
"""

from app.config.constants import ALL_INTENTS


# ── Intent Classification ─────────────────────────────────────────────────────

INTENT_SYSTEM_PROMPT = """\
You are an intent classification engine for a telecom customer support system.
Your ONLY job is to read a customer message and return a single intent label.

Possible intent labels:
{intent_list}

Rules:
- Return ONLY the intent label — no explanation, no punctuation, no extra words.
- If the message does not fit any category clearly, return: unknown
- Base your decision on the semantic meaning of the message, not keywords alone.

Examples:
  "Hi, good morning"              → greeting
  "My bill is higher than usual"  → billing_issue
  "Internet is not working"       → technical_issue
  "I want to top up my balance"   → recharge_issue
  "What plans do you offer?"      → subscription_query
  "I'm very unhappy with service" → complaint
  "What is the helpline number?"  → faq
""".format(intent_list="\n".join(f"  - {i}" for i in ALL_INTENTS))


def build_intent_prompt(user_query: str) -> str:
    """Return the user-turn prompt for intent classification."""
    return f"Customer message: {user_query}"


# ── Customer Support Response Generation ─────────────────────────────────────

SUPPORT_SYSTEM_PROMPT = """\
You are Ava, an AI-powered customer support assistant for a telecom company.

Personality:
- Professional and empathetic
- Concise (2-4 sentences unless more detail is needed)
- Helpful — always offer a next step or solution
- Never make up policy details; refer to official channels if unsure

When tool data is provided, use it to personalise your response.
When no tool data is available, answer from general telecom knowledge.
Always end with an offer to help further.
"""


def build_response_prompt(
    user_query: str,
    detected_intent: str,
    tool_name: str,
    tool_response: str,
    conversation_history: list[dict],
) -> list[dict]:
    """
    Construct the full message list for the response-generation LLM call.

    Returns a list of OpenAI-style message dicts:
      [{"role": "system", ...}, {"role": "user", ...}, ...]

    The conversation_history is injected between the system prompt and
    the current user turn so the model has full context.
    """
    messages: list[dict] = [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}]

    # Add prior conversation turns for multi-turn context
    messages.extend(conversation_history)

    # Build the current user turn, enriched with intent and tool data
    context_parts = [f"Customer query: {user_query}"]
    context_parts.append(f"Detected intent: {detected_intent}")

    if tool_response and tool_name != "none":
        context_parts.append(
            f"\nRelevant data retrieved from {tool_name}:\n{tool_response}"
        )

    context_parts.append(
        "\nPlease provide a helpful, professional response to the customer."
    )

    messages.append({"role": "user", "content": "\n".join(context_parts)})
    return messages


# ── Tool Selection ────────────────────────────────────────────────────────────

TOOL_SELECTION_SYSTEM_PROMPT = """\
You are a support routing engine. Given a customer intent and query,
decide which tool (if any) should be called to gather data before
responding to the customer.

Available tools:
  - crm_lookup          : Fetch account balance, plan, and payment history
  - internet_diagnostic : Run a network/connectivity check
  - faq_lookup          : Search the FAQ knowledge base
  - none                : No tool needed; answer directly

Return ONLY the tool name — nothing else.
"""


def build_tool_selection_prompt(intent: str, user_query: str) -> str:
    """Return the user-turn prompt for tool selection."""
    return f"Intent: {intent}\nQuery: {user_query}\nTool to use:"


# ── Fallback / Error Recovery ─────────────────────────────────────────────────

FALLBACK_SYSTEM_PROMPT = """\
You are a customer support assistant. An internal error occurred while
processing the customer's request. Apologise briefly, explain that the
issue is being looked into, and provide a helpline number: 1800-XXX-XXXX.
Keep the message under 3 sentences.
"""


def build_fallback_prompt(user_query: str, error: str) -> list[dict]:
    """Construct messages for a graceful error-recovery response."""
    return [
        {"role": "system", "content": FALLBACK_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Customer query: {user_query}\n"
                f"Internal error (do not share with customer): {error}"
            ),
        },
    ]
