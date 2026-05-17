"""
chat_window.py — Chat bubble rendering component.

Renders the conversation history as styled chat bubbles using
Streamlit's native st.chat_message() API (available since Streamlit 1.23).

Each message is displayed with a role-appropriate avatar and styling.
"""

import streamlit as st

from streamlit_app.utils.session_manager import get_messages


def render_chat_window() -> None:
    """
    Render all messages in the current session as chat bubbles.

    Uses Streamlit's st.chat_message() for clean, accessible chat UI.
    An empty-state placeholder is shown when no messages exist yet.
    """
    messages = get_messages()

    if not messages:
        # Empty state — shown on first load
        st.markdown(
            """
            <div style="
                text-align:center;
                padding:3rem 1rem;
                color:#888;
            ">
                <div style="font-size:3rem;">💬</div>
                <p style="margin-top:0.5rem; font-size:1.1rem;">
                    Start a conversation below or choose an example from the sidebar.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")

        with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
            st.markdown(content)


def render_thinking_indicator() -> st.empty:
    """
    Return an empty placeholder used to show a 'thinking…' animation
    while the agent is processing.  The caller should clear this
    placeholder once the response is ready.
    """
    placeholder = st.empty()
    with placeholder.container():
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("*Thinking…* ⏳")
    return placeholder
