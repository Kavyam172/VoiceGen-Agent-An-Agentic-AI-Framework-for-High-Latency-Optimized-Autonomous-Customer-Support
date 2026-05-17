"""
session_manager.py — Streamlit session state management.

Streamlit re-runs the entire script on every user interaction.
All mutable state that should persist across reruns must be stored in
st.session_state.  This module provides a clean API for initialising,
reading, and updating that state so the component files never have to
touch st.session_state keys directly.
"""

import streamlit as st
from app.config.constants import TOOL_NONE


# ── State key constants ───────────────────────────────────────────────────────
KEY_MESSAGES = "messages"               # List of chat messages for display
KEY_HISTORY = "conversation_history"   # LangChain-format history for the agent
KEY_INTENT = "last_intent"             # Most recently detected intent
KEY_TOOL = "last_tool"                 # Most recently used tool
KEY_TOOL_RESPONSE = "last_tool_response"
KEY_STEPS = "last_processing_steps"    # Execution steps for the status panel
KEY_ERROR = "last_error"               # Last error message (if any)
KEY_TURN = "turn_count"               # Number of completed turns


def init_session() -> None:
    """
    Initialise all session state keys to their default values.

    Safe to call on every Streamlit rerun — only sets keys that do
    not already exist, so existing state is preserved.
    """
    defaults = {
        KEY_MESSAGES: [],
        KEY_HISTORY: [],
        KEY_INTENT: "",
        KEY_TOOL: TOOL_NONE,
        KEY_TOOL_RESPONSE: "",
        KEY_STEPS: [],
        KEY_ERROR: "",
        KEY_TURN: 0,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def add_user_message(text: str) -> None:
    """Append a user message to the display message list."""
    st.session_state[KEY_MESSAGES].append({"role": "user", "content": text})


def add_assistant_message(text: str) -> None:
    """Append an assistant message to the display message list."""
    st.session_state[KEY_MESSAGES].append({"role": "assistant", "content": text})


def update_from_result(result: dict) -> None:
    """
    Persist an agent result dict into session state.

    Called after every successful agent.chat() call to keep the
    sidebar and status panel in sync.
    """
    st.session_state[KEY_HISTORY] = result.get("conversation_history", [])
    st.session_state[KEY_INTENT] = result.get("detected_intent", "")
    st.session_state[KEY_TOOL] = result.get("tool_name", TOOL_NONE)
    st.session_state[KEY_TOOL_RESPONSE] = result.get("tool_response", "")
    st.session_state[KEY_STEPS] = result.get("processing_steps", [])
    st.session_state[KEY_ERROR] = result.get("error", "")
    st.session_state[KEY_TURN] = st.session_state.get(KEY_TURN, 0) + 1


def clear_session() -> None:
    """Reset the session to its initial state (used by the Clear button)."""
    for key in [KEY_MESSAGES, KEY_HISTORY, KEY_INTENT, KEY_TOOL,
                KEY_TOOL_RESPONSE, KEY_STEPS, KEY_ERROR, KEY_TURN]:
        if key in st.session_state:
            del st.session_state[key]
    init_session()


def get_messages() -> list[dict]:
    """Return the current display message list."""
    return st.session_state.get(KEY_MESSAGES, [])


def get_history() -> list[dict]:
    """Return the LangChain-format conversation history."""
    return st.session_state.get(KEY_HISTORY, [])


def get_last_intent() -> str:
    return st.session_state.get(KEY_INTENT, "")


def get_last_tool() -> str:
    return st.session_state.get(KEY_TOOL, TOOL_NONE)


def get_last_tool_response() -> str:
    return st.session_state.get(KEY_TOOL_RESPONSE, "")


def get_processing_steps() -> list[str]:
    return st.session_state.get(KEY_STEPS, [])


def get_turn_count() -> int:
    return st.session_state.get(KEY_TURN, 0)


def get_last_error() -> str:
    return st.session_state.get(KEY_ERROR, "")
