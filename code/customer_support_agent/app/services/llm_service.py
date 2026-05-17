"""
llm_service.py — LLM initialisation and inference helpers.

Provides a single, lazily-initialised ChatOpenAI instance so the
rest of the codebase never has to worry about API keys or model params.

Design decisions:
  • Module-level singleton (_llm_instance) avoids re-creating the
    client on every function call, which is expensive.
  • All calls go through `call_llm()` — a thin wrapper that adds
    logging and basic error handling in one place.
  • The function accepts raw message dicts (OpenAI format) so it
    works seamlessly with the prompt templates in prompts.py.
"""

from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level singleton — initialised on first call to get_llm()
_llm_instance: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """
    Return the shared ChatOpenAI instance, creating it if necessary.

    Configuration is pulled from the centralised Settings object so
    the only thing callers need to ensure is that .env is loaded.
    """
    global _llm_instance

    if _llm_instance is None:
        logger.info(
            "Initialising LLM — model=%s temperature=%s",
            settings.model_name,
            settings.temperature,
        )
        _llm_instance = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    return _llm_instance


def call_llm(messages: list[dict]) -> str:
    """
    Invoke the LLM with a list of message dicts and return the text reply.

    Parameters
    ----------
    messages : list[dict]
        OpenAI-style message list, e.g.
        [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

    Returns
    -------
    str
        The model's text reply, stripped of leading/trailing whitespace.

    Raises
    ------
    RuntimeError
        If the LLM call fails (after propagating the underlying exception
        with an informative message for easier debugging).
    """
    llm = get_llm()

    # Convert plain dicts → LangChain message objects
    lc_messages: list[BaseMessage] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            lc_messages.append(SystemMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))

    logger.debug("Calling LLM with %d message(s)", len(lc_messages))

    try:
        response = llm.invoke(lc_messages)
        text = response.content.strip()
        logger.debug("LLM response (%d chars): %s…", len(text), text[:80])
        return text
    except Exception as exc:
        logger.error("LLM call failed: %s", exc, exc_info=True)
        raise RuntimeError(f"LLM call failed: {exc}") from exc


def call_llm_simple(system_prompt: str, user_message: str) -> str:
    """
    Convenience wrapper for the common system + user message pattern.

    Equivalent to:
        call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ])
    """
    return call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
    )
