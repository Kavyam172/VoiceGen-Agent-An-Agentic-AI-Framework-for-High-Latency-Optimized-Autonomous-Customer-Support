"""
state.py — LangGraph agent state definition.

AgentState is the single source of truth that flows through every node
in the LangGraph workflow.  Using TypedDict (rather than a plain dict)
gives us IDE autocompletion and makes the data contract between nodes
explicit.

Every node receives the *full* state and returns a *partial* update —
LangGraph merges the returned dict back into the running state.
"""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state object passed through the LangGraph workflow.

    Fields
    ------
    user_query : str
        The raw text message entered by the user.

    detected_intent : str
        The intent label returned by the intent-detection node.
        One of the values in constants.ALL_INTENTS.

    needs_tool : bool
        Set by the routing node. True when a tool call is required
        before generating the final response.

    tool_name : str
        The name of the tool selected by the routing node.
        One of constants.TOOL_* values, or TOOL_NONE.

    tool_response : str
        The raw string output returned by the executed tool.

    final_response : str
        The polished, customer-facing response produced by the
        response-generation node.

    conversation_history : list[dict]
        Accumulated list of {"role": "user"|"assistant", "content": str}
        message dicts.  Passed to the LLM for conversational context.

    processing_steps : list[str]
        Human-readable log of each graph step. Displayed in the
        Streamlit status panel for transparency / debugging.

    error : str
        Non-empty when an exception occurred inside a node.
        The response-generation node uses this to craft a graceful
        fallback message instead of crashing.
    """

    user_query: str
    detected_intent: str
    needs_tool: bool
    tool_name: str
    tool_response: str
    final_response: str
    conversation_history: list[dict]
    processing_steps: list[str]
    error: str


def create_initial_state(
    user_query: str,
    conversation_history: list[dict] | None = None,
) -> AgentState:
    """
    Build a fresh AgentState for a new user query.

    Callers pass the ongoing conversation_history so the agent has
    context from previous turns in the session.
    """
    return AgentState(
        user_query=user_query,
        detected_intent="",
        needs_tool=False,
        tool_name="none",
        tool_response="",
        final_response="",
        conversation_history=conversation_history or [],
        processing_steps=[],
        error="",
    )
