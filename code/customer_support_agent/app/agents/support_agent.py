"""
support_agent.py — High-level SupportAgent class.

This class is the public interface for the rest of the application.
It wraps the compiled LangGraph workflow and provides a clean, simple
`chat()` method that accepts a user message and returns a structured
result dict.

Callers (e.g. the Streamlit app, CLI runner, or test suite) should
interact with SupportAgent rather than importing the graph directly.
This decoupling means we can swap the underlying graph implementation
without touching any of the callers.
"""

from __future__ import annotations

from app.agents.state import AgentState, create_initial_state
from app.graph.assistant_graph import assistant_graph
from app.utils.helpers import truncate_history
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SupportAgent:
    """
    Stateless wrapper around the LangGraph customer support workflow.

    The agent itself is stateless — all conversational context is
    passed in via *conversation_history* and returned in the result
    dict for the caller to persist across turns.

    Usage
    -----
    >>> agent = SupportAgent()
    >>> result = agent.chat("My internet is down")
    >>> print(result["final_response"])
    """

    def chat(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """
        Process a single user message through the full LangGraph pipeline.

        Parameters
        ----------
        user_message : str
            The raw text entered by the customer.
        conversation_history : list[dict] | None
            Prior conversation turns as a list of
            {"role": "user"|"assistant", "content": str} dicts.
            Pass None or [] for the first turn.

        Returns
        -------
        dict with keys:
            final_response      — str: the assistant's reply
            detected_intent     — str: classified intent label
            tool_name           — str: tool used (or 'none')
            tool_response       — str: raw tool output (or '')
            conversation_history— list[dict]: updated history
            processing_steps    — list[str]: execution log
            error               — str: error message if something failed
        """
        logger.info("SupportAgent.chat() — message: %r", user_message[:80])

        # Trim history to avoid exceeding the model context window
        history = truncate_history(conversation_history or [], max_turns=10)

        # Build the initial state for this turn
        initial_state: AgentState = create_initial_state(
            user_query=user_message,
            conversation_history=history,
        )

        try:
            # Run the full LangGraph workflow synchronously
            final_state: AgentState = assistant_graph.invoke(initial_state)
        except Exception as exc:
            logger.error("Graph invocation failed: %s", exc, exc_info=True)
            # Return a safe fallback so the UI never sees a raw exception
            return {
                "final_response": (
                    "I'm sorry, something went wrong on our end. "
                    "Please try again or call 1800-XXX-XXXX."
                ),
                "detected_intent": "unknown",
                "tool_name": "none",
                "tool_response": "",
                "conversation_history": history,
                "processing_steps": [f"Fatal error: {exc}"],
                "error": str(exc),
            }

        logger.info(
            "SupportAgent.chat() complete — intent=%s tool=%s",
            final_state.get("detected_intent"),
            final_state.get("tool_name"),
        )

        return {
            "final_response": final_state.get("final_response", ""),
            "detected_intent": final_state.get("detected_intent", "unknown"),
            "tool_name": final_state.get("tool_name", "none"),
            "tool_response": final_state.get("tool_response", ""),
            "conversation_history": final_state.get("conversation_history", history),
            "processing_steps": final_state.get("processing_steps", []),
            "error": final_state.get("error", ""),
        }


# Module-level singleton for convenient import
support_agent = SupportAgent()
