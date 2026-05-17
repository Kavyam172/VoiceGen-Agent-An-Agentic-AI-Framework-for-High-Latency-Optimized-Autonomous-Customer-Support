"""
test_graph.py — Unit tests for the LangGraph workflow.

Tests the graph structure and node functions with mocked LLM calls.
This ensures the graph wiring is correct without making real API calls.

Run with:
    pytest tests/test_graph.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.agents.state import AgentState, create_initial_state
from app.config.constants import (
    TOOL_CRM,
    TOOL_NONE,
    INTENT_TECHNICAL,
    INTENT_BILLING,
    INTENT_GREETING,
    NODE_INTENT_DETECTION,
    NODE_TOOL_ROUTING,
    NODE_TOOL_EXECUTION,
    NODE_RESPONSE_GENERATION,
)


# ── Initial State Tests ───────────────────────────────────────────────────────

class TestAgentState:
    def test_create_initial_state_defaults(self):
        state = create_initial_state("Hello")
        assert state["user_query"] == "Hello"
        assert state["detected_intent"] == ""
        assert state["needs_tool"] is False
        assert state["tool_name"] == "none"
        assert state["tool_response"] == ""
        assert state["final_response"] == ""
        assert state["conversation_history"] == []
        assert state["processing_steps"] == []
        assert state["error"] == ""

    def test_create_initial_state_with_history(self):
        history = [{"role": "user", "content": "Hi"}]
        state = create_initial_state("Follow-up", conversation_history=history)
        assert state["conversation_history"] == history


# ── Node Tests (with mocked LLM) ──────────────────────────────────────────────

class TestIntentDetectionNode:
    @patch("app.graph.nodes.intent_service")
    def test_sets_detected_intent(self, mock_intent_service):
        mock_intent_service.classify.return_value = INTENT_BILLING

        from app.graph.nodes import intent_detection_node
        state = create_initial_state("What is my balance?")
        result = intent_detection_node(state)

        assert result["detected_intent"] == INTENT_BILLING
        assert len(result["processing_steps"]) > 0

    @patch("app.graph.nodes.intent_service")
    def test_handles_classification_error(self, mock_intent_service):
        mock_intent_service.classify.side_effect = RuntimeError("LLM error")

        from app.graph.nodes import intent_detection_node
        state = create_initial_state("Test query")
        result = intent_detection_node(state)

        assert result["detected_intent"] == "unknown"


class TestToolRoutingNode:
    def test_billing_intent_selects_crm_tool(self):
        from app.graph.nodes import tool_routing_node
        state = create_initial_state("What is my bill?")
        state["detected_intent"] = INTENT_BILLING

        result = tool_routing_node(state)

        assert result["needs_tool"] is True
        assert result["tool_name"] == TOOL_CRM

    def test_technical_intent_selects_internet_diagnostic(self):
        from app.graph.nodes import tool_routing_node
        from app.config.constants import TOOL_INTERNET_DIAG
        state = create_initial_state("My internet is slow")
        state["detected_intent"] = INTENT_TECHNICAL

        result = tool_routing_node(state)

        assert result["needs_tool"] is True
        assert result["tool_name"] == TOOL_INTERNET_DIAG

    def test_greeting_intent_needs_no_tool(self):
        from app.graph.nodes import tool_routing_node
        state = create_initial_state("Hello!")
        state["detected_intent"] = INTENT_GREETING

        result = tool_routing_node(state)

        assert result["needs_tool"] is False
        assert result["tool_name"] == TOOL_NONE


class TestToolExecutionNode:
    def test_crm_tool_executed_successfully(self):
        from app.graph.nodes import tool_execution_node
        state = create_initial_state("What is my balance?")
        state["tool_name"] = TOOL_CRM
        state["needs_tool"] = True

        result = tool_execution_node(state)

        assert "tool_response" in result
        assert len(result["tool_response"]) > 0

    def test_unknown_tool_returns_empty_response(self):
        from app.graph.nodes import tool_execution_node
        state = create_initial_state("Test")
        state["tool_name"] = "nonexistent_tool"
        state["needs_tool"] = True

        result = tool_execution_node(state)

        assert result["tool_response"] == ""


class TestResponseGenerationNode:
    @patch("app.graph.nodes.call_llm")
    def test_returns_final_response(self, mock_call_llm):
        mock_call_llm.return_value = "Your account balance is ₹245."

        from app.graph.nodes import response_generation_node
        state = create_initial_state("What is my balance?")
        state["detected_intent"] = INTENT_BILLING
        state["tool_name"] = TOOL_CRM
        state["tool_response"] = '{"balance": 245}'

        result = response_generation_node(state)

        assert result["final_response"] == "Your account balance is ₹245."
        assert len(result["conversation_history"]) == 2

    @patch("app.graph.nodes.call_llm")
    def test_updates_conversation_history(self, mock_call_llm):
        mock_call_llm.return_value = "Hello! How can I help?"

        from app.graph.nodes import response_generation_node
        state = create_initial_state("Hi")
        state["detected_intent"] = INTENT_GREETING
        state["tool_name"] = TOOL_NONE
        state["tool_response"] = ""

        result = response_generation_node(state)

        history = result["conversation_history"]
        assert history[-2]["role"] == "user"
        assert history[-2]["content"] == "Hi"
        assert history[-1]["role"] == "assistant"


# ── Graph Build Test ──────────────────────────────────────────────────────────

class TestGraphBuild:
    def test_graph_compiles_without_error(self):
        """Verify the graph can be compiled without raising any exceptions."""
        from app.graph.assistant_graph import build_graph
        graph = build_graph()
        assert graph is not None

    def test_graph_has_correct_nodes(self):
        from app.graph.assistant_graph import build_graph
        graph = build_graph()
        # The compiled graph should have our four nodes
        node_names = set(graph.get_graph().nodes.keys())
        assert NODE_INTENT_DETECTION in node_names
        assert NODE_TOOL_ROUTING in node_names
        assert NODE_TOOL_EXECUTION in node_names
        assert NODE_RESPONSE_GENERATION in node_names
