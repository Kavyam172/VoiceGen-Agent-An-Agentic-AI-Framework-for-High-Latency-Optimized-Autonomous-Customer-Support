"""
main.py — CLI entry point for the Customer Support AI Assistant.

Run from the project root with:
    python -m app.main

This interactive REPL lets you test the full LangGraph pipeline from
the terminal without needing to start the Streamlit frontend.
Useful for rapid testing and integration checks.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so relative imports work when
# this file is run directly (python app/main.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.agents.support_agent import SupportAgent
from app.config.constants import INTENT_DISPLAY_NAMES, TOOL_DISPLAY_NAMES
from app.utils.logger import get_logger

logger = get_logger(__name__)

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         Customer Support AI Assistant — CLI Mode            ║
║         Powered by LangGraph + OpenAI                       ║
║         Type 'quit' or 'exit' to end the session            ║
╚══════════════════════════════════════════════════════════════╝
"""

SEPARATOR = "─" * 64


def run_cli() -> None:
    """
    Interactive command-line loop for the support assistant.

    Maintains conversation history across turns so the agent has
    multi-turn context, just as in the Streamlit frontend.
    """
    print(BANNER)

    agent = SupportAgent()
    conversation_history: list[dict] = []
    turn = 0

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "bye", "q"}:
            print("\nThank you for contacting support. Goodbye!")
            break

        turn += 1
        print(f"\n{SEPARATOR}")
        print(f"Processing… [Turn {turn}]")

        result = agent.chat(
            user_message=user_input,
            conversation_history=conversation_history,
        )

        # Update history for the next turn
        conversation_history = result["conversation_history"]

        # Display diagnostic info
        intent_label = INTENT_DISPLAY_NAMES.get(
            result["detected_intent"], result["detected_intent"]
        )
        tool_label = TOOL_DISPLAY_NAMES.get(result["tool_name"], result["tool_name"])

        print(f"Intent  : {intent_label}")
        print(f"Tool    : {tool_label}")

        if result.get("error"):
            print(f"⚠ Error : {result['error']}")

        print(f"{SEPARATOR}")
        print(f"\nAssistant: {result['final_response']}")

        # Optionally show processing steps
        if "--debug" in sys.argv:
            print(f"\n[Debug] Processing steps:")
            for step in result.get("processing_steps", []):
                print(f"  • {step}")


if __name__ == "__main__":
    run_cli()
