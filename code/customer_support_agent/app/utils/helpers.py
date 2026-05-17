"""
helpers.py — Shared utility functions used across the project.

Keep this module small and stateless — pure functions only.
"""

import json
import re
from datetime import datetime
from typing import Any


def safe_json_loads(text: str) -> dict | None:
    """
    Attempt to parse a JSON string.

    Returns the parsed dict on success, or None on failure.
    Useful when LLM responses may occasionally return malformed JSON.
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_block(text: str) -> str:
    """
    Extract the first JSON object found inside a larger string.

    LLMs sometimes wrap JSON in markdown code fences or add extra prose.
    This helper strips that wrapping so json.loads() can parse cleanly.
    """
    # Remove ```json ... ``` fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)

    # Fall back to first bare { … } block
    bare = re.search(r"(\{.*\})", text, re.DOTALL)
    if bare:
        return bare.group(1)

    return text


def format_tool_response(tool_name: str, data: Any) -> str:
    """
    Pretty-format a tool's output for inclusion in an LLM prompt.

    Converts the data to an indented JSON string with a header line so
    the model understands the provenance of the information.
    """
    formatted = json.dumps(data, indent=2, default=str)
    return f"[Tool: {tool_name}]\n{formatted}"


def truncate_history(
    history: list[dict], max_turns: int = 10
) -> list[dict]:
    """
    Keep only the last *max_turns* conversation turns to avoid exceeding
    the model's context window.

    Each turn is a dict with 'role' and 'content' keys (standard
    OpenAI/LangChain message format).
    """
    if len(history) <= max_turns * 2:
        return history
    # Always keep at least the last max_turns * 2 messages
    return history[-(max_turns * 2):]


def current_timestamp() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def intent_to_emoji(intent: str) -> str:
    """Map an intent string to a display emoji for the Streamlit UI."""
    mapping = {
        "greeting": "👋",
        "billing_issue": "💳",
        "technical_issue": "🔧",
        "recharge_issue": "🔄",
        "faq": "❓",
        "complaint": "⚠️",
        "subscription_query": "📋",
        "unknown": "🤔",
    }
    return mapping.get(intent, "💬")
