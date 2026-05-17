"""
sidebar.py — Streamlit sidebar component.

Renders:
  • Model and version info
  • Current session statistics
  • Detected intent badge
  • Active tool indicator
  • Example queries (clickable)
  • Clear session button
"""

import streamlit as st

from app.config.constants import (
    INTENT_DISPLAY_NAMES,
    TOOL_DISPLAY_NAMES,
    EXAMPLE_QUERIES,
)
from app.config.settings import settings
from app.utils.helpers import intent_to_emoji
from streamlit_app.utils.session_manager import (
    clear_session,
    get_last_intent,
    get_last_tool,
    get_turn_count,
    get_last_error,
    get_processing_steps,
    get_last_tool_response,
)


# ── Intent badge colour mapping ───────────────────────────────────────────────
_INTENT_COLOURS: dict[str, str] = {
    "greeting": "#4CAF50",
    "billing_issue": "#FF9800",
    "technical_issue": "#2196F3",
    "recharge_issue": "#9C27B0",
    "faq": "#00BCD4",
    "complaint": "#F44336",
    "subscription_query": "#3F51B5",
    "unknown": "#9E9E9E",
}


def render_sidebar() -> str | None:
    """
    Render the full sidebar and return an example query if one was clicked.

    Returns
    -------
    str | None
        The example query string if the user clicked one, otherwise None.
    """
    with st.sidebar:
        # ── Branding ─────────────────────────────────────────────────────────
        st.markdown("## 🤖 Support Assistant")
        st.caption(f"v{settings.app_version}")
        st.divider()

        # ── Model Info ────────────────────────────────────────────────────────
        st.markdown("### Model Info")
        st.markdown(f"**Model:** `{settings.model_name}`")
        st.markdown(f"**Temperature:** `{settings.temperature}`")
        st.markdown(f"**Max Tokens:** `{settings.max_tokens}`")
        st.divider()

        # ── Session Stats ─────────────────────────────────────────────────────
        st.markdown("### Session")
        turns = get_turn_count()
        st.metric("Turns", turns)

        # ── Intent Badge ──────────────────────────────────────────────────────
        st.markdown("### Detected Intent")
        intent = get_last_intent()
        if intent:
            colour = _INTENT_COLOURS.get(intent, "#9E9E9E")
            emoji = intent_to_emoji(intent)
            label = INTENT_DISPLAY_NAMES.get(intent, intent)
            st.markdown(
                f"""<div style="
                    background-color:{colour}22;
                    border-left:4px solid {colour};
                    padding:8px 12px;
                    border-radius:4px;
                    font-weight:600;
                    color:{colour};
                ">{emoji} {label}</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.caption("No query processed yet.")

        st.divider()

        # ── Tool Info ─────────────────────────────────────────────────────────
        st.markdown("### Active Tool")
        tool = get_last_tool()
        tool_label = TOOL_DISPLAY_NAMES.get(tool, tool)
        if tool and tool != "none":
            st.markdown(f"🔧 `{tool_label}`")
            tool_response = get_last_tool_response()
            if tool_response:
                with st.expander("View tool output", expanded=False):
                    st.code(tool_response, language="json")
        else:
            st.caption("No tool invoked.")

        st.divider()

        # ── Processing Steps ──────────────────────────────────────────────────
        steps = get_processing_steps()
        if steps:
            with st.expander("Graph execution steps", expanded=False):
                for step in steps:
                    st.markdown(f"• {step}")

        # ── Error Banner ──────────────────────────────────────────────────────
        error = get_last_error()
        if error:
            st.error(f"⚠ {error}")

        st.divider()

        # ── Example Queries ───────────────────────────────────────────────────
        st.markdown("### Try an Example")
        clicked_query: str | None = None
        for query in EXAMPLE_QUERIES:
            if st.button(query, key=f"ex_{query[:20]}", use_container_width=True):
                clicked_query = query

        st.divider()

        # ── Clear Button ──────────────────────────────────────────────────────
        if st.button("🗑 Clear Conversation", use_container_width=True, type="secondary"):
            clear_session()
            st.rerun()

        st.caption("Built with LangGraph + Streamlit")

    return clicked_query
