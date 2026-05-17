"""
status_panel.py — Live workflow status panel component.

Renders a visual indicator of the LangGraph pipeline showing which
nodes have been executed in the most recent turn.

Displayed as a compact horizontal stepper below the header.
"""

import streamlit as st

from app.config.constants import (
    NODE_INTENT_DETECTION,
    NODE_TOOL_ROUTING,
    NODE_TOOL_EXECUTION,
    NODE_RESPONSE_GENERATION,
    INTENT_DISPLAY_NAMES,
    TOOL_DISPLAY_NAMES,
)
from streamlit_app.utils.session_manager import (
    get_last_intent,
    get_last_tool,
    get_processing_steps,
    get_turn_count,
)

# Node display order for the pipeline stepper
_PIPELINE_STEPS = [
    (NODE_INTENT_DETECTION, "Intent Detection"),
    (NODE_TOOL_ROUTING, "Tool Routing"),
    (NODE_TOOL_EXECUTION, "Tool Execution"),
    (NODE_RESPONSE_GENERATION, "Response Generation"),
]


def render_status_panel() -> None:
    """
    Render the workflow status panel.

    Shows:
      - Whether each pipeline stage was executed in the last turn
      - The detected intent and active tool as metric cards
    """
    if get_turn_count() == 0:
        return

    steps = get_processing_steps()
    intent = get_last_intent()
    tool = get_last_tool()

    # ── Pipeline Stepper ──────────────────────────────────────────────────────
    with st.expander("📊 Last Graph Execution", expanded=False):
        cols = st.columns(len(_PIPELINE_STEPS))

        for col, (node_id, label) in zip(cols, _PIPELINE_STEPS):
            # Check if this node appears in the processing steps
            executed = any(
                label.lower() in step.lower() for step in steps
            )
            with col:
                if executed:
                    st.markdown(
                        f"""<div style="
                            text-align:center;
                            padding:8px 4px;
                            background:#e8f5e9;
                            border-radius:8px;
                            border:1px solid #4CAF50;
                        ">
                            <div style="font-size:1.2rem;">✅</div>
                            <div style="font-size:0.75rem; color:#2e7d32; font-weight:600;">{label}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""<div style="
                            text-align:center;
                            padding:8px 4px;
                            background:#f5f5f5;
                            border-radius:8px;
                            border:1px solid #ccc;
                        ">
                            <div style="font-size:1.2rem;">⬜</div>
                            <div style="font-size:0.75rem; color:#999;">{label}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

        # ── Summary metrics ───────────────────────────────────────────────────
        st.divider()
        m1, m2 = st.columns(2)
        with m1:
            intent_label = INTENT_DISPLAY_NAMES.get(intent, intent or "—")
            st.metric("Detected Intent", intent_label)
        with m2:
            tool_label = TOOL_DISPLAY_NAMES.get(tool, tool or "—")
            st.metric("Tool Used", tool_label)
