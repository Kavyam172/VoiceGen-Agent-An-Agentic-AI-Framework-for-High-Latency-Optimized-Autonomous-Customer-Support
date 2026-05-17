"""
app.py — Main Streamlit application entry point.

Run with:
    streamlit run streamlit_app/app.py
    (from the customer_support_agent/ directory)

This file orchestrates the full Streamlit UI:
  1. Load custom CSS
  2. Render the header
  3. Render the sidebar (and capture any clicked example query)
  4. Render the status panel
  5. Render the chat history
  6. Handle new user input via st.chat_input()
  7. Invoke the SupportAgent and update session state
"""

import os
import re
import sys
from pathlib import Path

# ── Path & working-directory setup ───────────────────────────────────────────
# This block runs before any project imports so it is CWD-agnostic.
# It works correctly whether the user runs:
#   streamlit run streamlit_app/app.py          (from customer_support_agent/)
#   python run.py                               (from any directory)
#   streamlit run customer_support_agent/...    (from final_eval/)

# app.py  →  streamlit_app/  →  customer_support_agent/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Put the project root on sys.path so "from app.xxx import yyy" resolves.
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Change the working directory to the project root so that any code that
# uses relative paths (e.g. open(".env"), glob("*.py")) finds them correctly.
os.chdir(_PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(_PROJECT_ROOT / ".env")

import streamlit as st

from app.agents.support_agent import SupportAgent
from app.config.settings import settings
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.chat_window import render_chat_window, render_thinking_indicator
from streamlit_app.components.status_panel import render_status_panel
from streamlit_app.utils.session_manager import (
    init_session,
    add_user_message,
    add_assistant_message,
    update_from_result,
    get_history,
)

# ── Page config — must be the very first Streamlit call ──────────────────────
st.set_page_config(
    page_title=settings.app_name,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load custom CSS ───────────────────────────────────────────────────────────
_CSS_PATH = Path(__file__).parent / "assets" / "styles.css"
if _CSS_PATH.exists():
    with open(_CSS_PATH, encoding="utf-8") as f:
        _raw_css = f.read()
    # Strip all /* ... */ block comments before injection.
    # CSS comments containing "--" sequences confuse Streamlit's HTML
    # sanitizer, which mistakes them for HTML comment delimiters and
    # prematurely closes the <style> block, leaking the rest as visible text.
    _clean_css = re.sub(r"/\*.*?\*/", "", _raw_css, flags=re.DOTALL).strip()
    st.markdown(f"<style>{_clean_css}</style>", unsafe_allow_html=True)

# ── Initialise session state ──────────────────────────────────────────────────
init_session()

# ── Agent singleton (cached so it's not re-created on every rerun) ────────────
@st.cache_resource
def get_agent() -> SupportAgent:
    return SupportAgent()


agent = get_agent()

# ── Sidebar ───────────────────────────────────────────────────────────────────
example_query = render_sidebar()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="app-header">
        <h1>🤖 {settings.app_name}</h1>
        <p>AI-powered telecom support powered by LangGraph agentic workflow</p>
        <span class="badge">⚡ LangGraph · LangChain · OpenAI · Streamlit</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Workflow explanation ──────────────────────────────────────────────────────
with st.expander("ℹ️ How it works — LangGraph Workflow", expanded=False):
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            """
            **Agentic Pipeline (left to right):**

            1. **Intent Detection** — The LLM classifies your message into a support intent
               (billing, technical, FAQ, etc.) using a constrained prompt.

            2. **Tool Routing** — A routing node decides whether a tool call is needed
               based on the detected intent.

            3. **Tool Execution** — If needed, one of three tools is invoked:
               - `CRM Lookup` — fetches account/billing data
               - `Internet Diagnostic` — runs a network check
               - `FAQ Lookup` — searches the knowledge base

            4. **Response Generation** — The LLM synthesises all available context
               (intent + tool data + history) into a professional reply.
            """
        )
    with col2:
        st.markdown(
            """
            ```
            User Query
                ↓
            Intent Detection
                ↓
            Tool Routing
            ↙           ↘
            Tool Exec   (skip)
                ↘       ↙
            Response Generation
                ↓
            Final Reply
            ```
            """
        )

st.divider()

# ── Status Panel ──────────────────────────────────────────────────────────────
render_status_panel()

# ── Chat Window ───────────────────────────────────────────────────────────────
render_chat_window()

# ── Process example query if one was clicked from the sidebar ─────────────────
if example_query:
    # Treat it exactly like a typed user message
    st.session_state["_pending_input"] = example_query

# ── Chat Input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("Type your support query here…")

# Merge pending input (from example button click) with the chat input field
if not user_input and st.session_state.get("_pending_input"):
    user_input = st.session_state.pop("_pending_input")

# ── Handle new message ────────────────────────────────────────────────────────
if user_input:
    user_input = user_input.strip()
    if not user_input:
        st.stop()

    # Show the user's message immediately
    add_user_message(user_input)

    # Render the thinking indicator while the agent processes
    thinking_placeholder = render_thinking_indicator()

    # Invoke the agent
    with st.spinner(""):
        result = agent.chat(
            user_message=user_input,
            conversation_history=get_history(),
        )

    # Clear the thinking indicator
    thinking_placeholder.empty()

    # Persist results into session state
    update_from_result(result)
    add_assistant_message(result["final_response"])

    # Rerun to refresh the chat window and sidebar with updated state
    st.rerun()
