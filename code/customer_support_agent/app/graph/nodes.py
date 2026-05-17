"""
nodes.py — LangGraph node functions for the support assistant workflow.

Each function in this module is a *node* in the LangGraph state machine.
Nodes follow the LangGraph contract:
  - Accept the full AgentState as input
  - Return a partial dict whose keys are merged into the running state

The four nodes implement the pipeline:
  1. intent_detection_node  — classify the user's intent via LLM
  2. tool_routing_node      — decide which tool (if any) to invoke
  3. tool_execution_node    — call the selected tool and capture output
  4. response_generation_node — generate the final customer-facing reply

A module-level TOOL_REGISTRY maps tool names → callable, making it
trivial to add new tools without modifying the graph wiring.
"""

from app.agents.state import AgentState
from app.agents.prompts import (
    build_response_prompt,
    build_fallback_prompt,
    TOOL_SELECTION_SYSTEM_PROMPT,
    build_tool_selection_prompt,
)
from app.config.constants import (
    INTENT_TOOL_MAP,
    TOOL_NONE,
    TOOL_CRM,
    TOOL_INTERNET_DIAG,
    TOOL_FAQ,
    FALLBACK_RESPONSE,
)
from app.services.intent_service import intent_service
from app.services.llm_service import call_llm, call_llm_simple
from app.tools.dummy_crm_tool import crm_lookup
from app.tools.internet_diagnostic_tool import internet_diagnostic
from app.tools.faq_tool import faq_lookup
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Tool Registry ─────────────────────────────────────────────────────────────
# Maps the tool name string → the callable LangChain tool.
# Adding a new tool requires only a single entry here.
TOOL_REGISTRY: dict[str, any] = {
    TOOL_CRM: crm_lookup,
    TOOL_INTERNET_DIAG: internet_diagnostic,
    TOOL_FAQ: faq_lookup,
}


# ── Node 1 — Intent Detection ─────────────────────────────────────────────────

def intent_detection_node(state: AgentState) -> dict:
    """
    Classify the user's query into one of the supported intent labels.

    Uses IntentService (which calls the LLM with a constrained prompt)
    so classification is semantic rather than keyword-based.

    State keys updated: detected_intent, processing_steps
    """
    user_query = state.get("user_query", "")
    steps = list(state.get("processing_steps", []))

    logger.info("[Node] intent_detection_node — query: %r", user_query[:60])
    steps.append("Intent Detection: analysing customer query…")

    try:
        intent = intent_service.classify(user_query)
    except Exception as exc:
        logger.error("Intent detection failed: %s", exc)
        intent = "unknown"

    steps.append(f"Intent Detection: detected → {intent}")
    logger.info("[Node] intent_detection_node complete — intent=%s", intent)

    return {
        "detected_intent": intent,
        "processing_steps": steps,
    }


# ── Node 2 — Tool Routing ─────────────────────────────────────────────────────

def tool_routing_node(state: AgentState) -> dict:
    """
    Decide whether a tool call is needed and, if so, which tool to use.

    Routing strategy (two-tier):
      1. Check the static INTENT_TOOL_MAP for a deterministic mapping.
      2. If the map returns TOOL_NONE but the query might benefit from a
         tool, ask the LLM to confirm.  This keeps routing predictable for
         common intents while remaining flexible for edge cases.

    State keys updated: needs_tool, tool_name, processing_steps
    """
    intent = state.get("detected_intent", "unknown")
    user_query = state.get("user_query", "")
    steps = list(state.get("processing_steps", []))

    logger.info("[Node] tool_routing_node — intent=%s", intent)
    steps.append(f"Tool Routing: evaluating tool need for intent '{intent}'…")

    # Tier-1: deterministic lookup
    mapped_tool = INTENT_TOOL_MAP.get(intent, TOOL_NONE)

    if mapped_tool != TOOL_NONE:
        steps.append(f"Tool Routing: selected tool → {mapped_tool} (rule-based)")
        logger.info("[Node] tool_routing_node — tool=%s (rule-based)", mapped_tool)
        return {
            "needs_tool": True,
            "tool_name": mapped_tool,
            "processing_steps": steps,
        }

    # Tier-2: LLM decides for ambiguous / unknown intents
    try:
        llm_tool = call_llm_simple(
            system_prompt=TOOL_SELECTION_SYSTEM_PROMPT,
            user_message=build_tool_selection_prompt(intent, user_query),
        ).strip().lower()
    except Exception as exc:
        logger.warning("LLM tool-selection failed: %s — defaulting to none", exc)
        llm_tool = TOOL_NONE

    if llm_tool in TOOL_REGISTRY:
        steps.append(f"Tool Routing: selected tool → {llm_tool} (LLM-based)")
        logger.info("[Node] tool_routing_node — tool=%s (LLM-based)", llm_tool)
        return {
            "needs_tool": True,
            "tool_name": llm_tool,
            "processing_steps": steps,
        }

    steps.append("Tool Routing: no tool required — direct response")
    logger.info("[Node] tool_routing_node — no tool needed")
    return {
        "needs_tool": False,
        "tool_name": TOOL_NONE,
        "processing_steps": steps,
    }


# ── Node 3 — Tool Execution ───────────────────────────────────────────────────

def tool_execution_node(state: AgentState) -> dict:
    """
    Execute the selected tool and store its output in the state.

    The tool is looked up from TOOL_REGISTRY by name and invoked.
    All tool exceptions are caught so a single failed tool call does
    not crash the entire graph — the response node will handle the
    empty tool_response gracefully.

    State keys updated: tool_response, processing_steps, error (on failure)
    """
    tool_name = state.get("tool_name", TOOL_NONE)
    user_query = state.get("user_query", "")
    steps = list(state.get("processing_steps", []))

    logger.info("[Node] tool_execution_node — tool=%s", tool_name)
    steps.append(f"Tool Execution: invoking '{tool_name}'…")

    tool_fn = TOOL_REGISTRY.get(tool_name)

    if tool_fn is None:
        steps.append(f"Tool Execution: tool '{tool_name}' not found — skipping")
        logger.warning("[Node] tool_execution_node — unknown tool: %s", tool_name)
        return {"tool_response": "", "processing_steps": steps}

    try:
        # LangChain @tool functions accept a single string argument.
        # We pass a sensible default; real systems would extract a customer
        # identifier from the conversation context or session.
        if tool_name == TOOL_CRM:
            tool_response = tool_fn.invoke({"customer_id": "C001"})
        elif tool_name == TOOL_INTERNET_DIAG:
            tool_response = tool_fn.invoke({"area_code": "110001"})
        elif tool_name == TOOL_FAQ:
            tool_response = tool_fn.invoke({"query": user_query})
        else:
            tool_response = tool_fn.invoke({"query": user_query})

        steps.append(f"Tool Execution: '{tool_name}' returned successfully")
        logger.info("[Node] tool_execution_node — tool succeeded")
        return {
            "tool_response": str(tool_response),
            "processing_steps": steps,
        }

    except Exception as exc:
        error_msg = f"Tool execution error ({tool_name}): {exc}"
        logger.error("[Node] %s", error_msg, exc_info=True)
        steps.append(f"Tool Execution: error — {exc}")
        return {
            "tool_response": "",
            "processing_steps": steps,
            "error": error_msg,
        }


# ── Node 4 — Response Generation ─────────────────────────────────────────────

def response_generation_node(state: AgentState) -> dict:
    """
    Generate the final customer-facing response using the LLM.

    Combines:
      - The user's original query
      - The detected intent
      - Any tool output (if a tool was run)
      - The conversation history (for multi-turn context)

    If an error is present in the state (e.g. a failed tool call),
    the node falls back to a graceful apology message generated by a
    separate fallback prompt.

    State keys updated: final_response, processing_steps,
                        conversation_history
    """
    user_query = state.get("user_query", "")
    intent = state.get("detected_intent", "unknown")
    tool_name = state.get("tool_name", TOOL_NONE)
    tool_response = state.get("tool_response", "")
    history = list(state.get("conversation_history", []))
    error = state.get("error", "")
    steps = list(state.get("processing_steps", []))

    logger.info("[Node] response_generation_node — intent=%s error=%r", intent, bool(error))
    steps.append("Response Generation: composing reply…")

    try:
        if error and not tool_response:
            # Use the fallback prompt when something went wrong upstream
            messages = build_fallback_prompt(user_query, error)
        else:
            messages = build_response_prompt(
                user_query=user_query,
                detected_intent=intent,
                tool_name=tool_name,
                tool_response=tool_response,
                conversation_history=history,
            )

        final_response = call_llm(messages)

    except Exception as exc:
        logger.error("[Node] response_generation_node failed: %s", exc, exc_info=True)
        final_response = FALLBACK_RESPONSE

    # Append this turn to the conversation history for future turns
    updated_history = history + [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": final_response},
    ]

    steps.append("Response Generation: complete")
    logger.info("[Node] response_generation_node complete")

    return {
        "final_response": final_response,
        "conversation_history": updated_history,
        "processing_steps": steps,
    }
