"""
assistant_graph.py — LangGraph workflow definition.

This module builds and compiles the directed state graph that powers
the customer support assistant.

Graph topology
--------------

    START
      │
      ▼
    intent_detection_node
      │
      ▼
    tool_routing_node
      │
      ├─ needs_tool=True ──► tool_execution_node ──► response_generation_node
      │
      └─ needs_tool=False ──────────────────────────► response_generation_node
                                                              │
                                                             END

The single conditional edge after tool_routing_node is the only branching
point in the graph, keeping the architecture simple while still
demonstrating proper LangGraph conditional routing.
"""

from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.config.constants import (
    NODE_INTENT_DETECTION,
    NODE_TOOL_ROUTING,
    NODE_TOOL_EXECUTION,
    NODE_RESPONSE_GENERATION,
)
from app.graph.nodes import (
    intent_detection_node,
    tool_routing_node,
    tool_execution_node,
    response_generation_node,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _route_after_tool_routing(state: AgentState) -> str:
    """
    Conditional edge function.

    Returns the name of the *next* node based on whether the routing
    node decided a tool call is needed.

    LangGraph calls this function with the current state after
    tool_routing_node completes and uses the returned string to
    determine which node to visit next.
    """
    if state.get("needs_tool", False):
        return NODE_TOOL_EXECUTION
    return NODE_RESPONSE_GENERATION


def build_graph() -> StateGraph:
    """
    Construct and compile the LangGraph StateGraph.

    Returns
    -------
    CompiledGraph
        A compiled, executable LangGraph graph.  Call `.invoke(state)`
        or `.stream(state)` on this object to run the workflow.
    """
    logger.info("Building LangGraph assistant workflow…")

    # Initialise the graph with our AgentState schema
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node(NODE_INTENT_DETECTION, intent_detection_node)
    graph.add_node(NODE_TOOL_ROUTING, tool_routing_node)
    graph.add_node(NODE_TOOL_EXECUTION, tool_execution_node)
    graph.add_node(NODE_RESPONSE_GENERATION, response_generation_node)

    # ── Wire edges ────────────────────────────────────────────────────────────

    # Entry point: START → intent detection
    graph.add_edge(START, NODE_INTENT_DETECTION)

    # After intent detection: always proceed to tool routing
    graph.add_edge(NODE_INTENT_DETECTION, NODE_TOOL_ROUTING)

    # After tool routing: branch based on needs_tool flag
    graph.add_conditional_edges(
        NODE_TOOL_ROUTING,
        _route_after_tool_routing,
        {
            NODE_TOOL_EXECUTION: NODE_TOOL_EXECUTION,
            NODE_RESPONSE_GENERATION: NODE_RESPONSE_GENERATION,
        },
    )

    # After tool execution: always go to response generation
    graph.add_edge(NODE_TOOL_EXECUTION, NODE_RESPONSE_GENERATION)

    # After response generation: end the graph
    graph.add_edge(NODE_RESPONSE_GENERATION, END)

    # ── Compile ───────────────────────────────────────────────────────────────
    compiled = graph.compile()
    logger.info("LangGraph workflow compiled successfully")
    return compiled


# Module-level compiled graph — import this singleton from other modules
# to avoid rebuilding the graph on every request.
assistant_graph = build_graph()
