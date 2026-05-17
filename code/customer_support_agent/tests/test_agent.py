"""
test_agent.py — Integration tests for the SupportAgent class.

These tests mock the underlying LangGraph workflow to verify the
SupportAgent's public API, error handling, and session management
without making real LLM or tool calls.

Run with:
    pytest tests/test_agent.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.agents.support_agent import SupportAgent
from app.config.constants import INTENT_BILLING, TOOL_CRM, TOOL_NONE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_mock_state(
    intent: str = INTENT_BILLING,
    tool: str = TOOL_CRM,
    response: str = "Your balance is ₹245.",
    error: str = "",
) -> dict:
    """Build a fake final state dict for mocking assistant_graph.invoke."""
    return {
        "user_query": "What is my balance?",
        "detected_intent": intent,
        "needs_tool": tool != TOOL_NONE,
        "tool_name": tool,
        "tool_response": '{"balance": 245}' if tool != TOOL_NONE else "",
        "final_response": response,
        "conversation_history": [
            {"role": "user", "content": "What is my balance?"},
            {"role": "assistant", "content": response},
        ],
        "processing_steps": [
            "Intent Detection: detected → billing_issue",
            "Tool Routing: selected tool → crm_lookup",
            "Tool Execution: 'crm_lookup' returned successfully",
            "Response Generation: complete",
        ],
        "error": error,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSupportAgentAPI:
    @patch("app.agents.support_agent.assistant_graph")
    def test_chat_returns_required_keys(self, mock_graph):
        mock_graph.invoke.return_value = _make_mock_state()

        agent = SupportAgent()
        result = agent.chat("What is my balance?")

        required_keys = [
            "final_response",
            "detected_intent",
            "tool_name",
            "tool_response",
            "conversation_history",
            "processing_steps",
            "error",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    @patch("app.agents.support_agent.assistant_graph")
    def test_chat_returns_correct_response(self, mock_graph):
        mock_graph.invoke.return_value = _make_mock_state(
            response="Your account balance is ₹245.50."
        )

        agent = SupportAgent()
        result = agent.chat("Check my balance")

        assert result["final_response"] == "Your account balance is ₹245.50."

    @patch("app.agents.support_agent.assistant_graph")
    def test_chat_passes_history_to_graph(self, mock_graph):
        mock_graph.invoke.return_value = _make_mock_state()
        history = [{"role": "user", "content": "Hi"}]

        agent = SupportAgent()
        agent.chat("What is my bill?", conversation_history=history)

        # Verify the graph was invoked with state containing the history
        call_args = mock_graph.invoke.call_args[0][0]
        assert call_args["conversation_history"] == history

    @patch("app.agents.support_agent.assistant_graph")
    def test_chat_handles_graph_exception(self, mock_graph):
        mock_graph.invoke.side_effect = Exception("Unexpected graph error")

        agent = SupportAgent()
        result = agent.chat("Test query")

        # Should return a graceful fallback, not raise
        assert "final_response" in result
        assert len(result["final_response"]) > 0
        assert result["error"] != ""

    @patch("app.agents.support_agent.assistant_graph")
    def test_chat_truncates_long_history(self, mock_graph):
        mock_graph.invoke.return_value = _make_mock_state()

        # Build a history with 30 turns (60 messages)
        long_history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(60)
        ]

        agent = SupportAgent()
        agent.chat("Test", conversation_history=long_history)

        # The graph should have been called with a truncated history (≤ 20 msgs)
        call_args = mock_graph.invoke.call_args[0][0]
        assert len(call_args["conversation_history"]) <= 20

    @patch("app.agents.support_agent.assistant_graph")
    def test_chat_empty_message_still_processed(self, mock_graph):
        mock_graph.invoke.return_value = _make_mock_state(intent="unknown")

        agent = SupportAgent()
        result = agent.chat("")

        assert "final_response" in result


class TestSupportAgentStatelessness:
    @patch("app.agents.support_agent.assistant_graph")
    def test_two_calls_are_independent(self, mock_graph):
        """The agent should not carry state between calls internally."""
        mock_graph.invoke.side_effect = [
            _make_mock_state(intent=INTENT_BILLING, response="Balance: ₹245"),
            _make_mock_state(intent="technical_issue", response="Running diagnostics…"),
        ]

        agent = SupportAgent()
        result1 = agent.chat("What is my balance?")
        result2 = agent.chat("My internet is down")

        assert result1["detected_intent"] == INTENT_BILLING
        assert result2["detected_intent"] == "technical_issue"
        assert result1["final_response"] != result2["final_response"]
