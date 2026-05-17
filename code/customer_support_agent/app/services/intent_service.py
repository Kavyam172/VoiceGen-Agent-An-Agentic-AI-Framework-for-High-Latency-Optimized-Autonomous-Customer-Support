"""
intent_service.py — LLM-powered intent classification.

The IntentService sends the user query to the LLM with a tightly
constrained classification prompt and returns one of the canonical
intent labels defined in constants.py.

Key design choices:
  • The LLM is asked to return ONLY the intent label — no JSON, no
    explanation — which makes parsing trivial and reliable.
  • A post-processing step validates the returned label against the
    known list and falls back to INTENT_UNKNOWN if the LLM goes
    off-script.
  • The service is a plain class (not a singleton) so it can be
    easily mocked in tests.
"""

from app.agents.prompts import INTENT_SYSTEM_PROMPT, build_intent_prompt
from app.config.constants import ALL_INTENTS, INTENT_UNKNOWN
from app.services.llm_service import call_llm_simple
from app.utils.logger import get_logger

logger = get_logger(__name__)


class IntentService:
    """Classifies a user query into one of the supported intent labels."""

    def classify(self, user_query: str) -> str:
        """
        Classify *user_query* and return an intent label.

        Parameters
        ----------
        user_query : str
            Raw text from the customer.

        Returns
        -------
        str
            One of the values in constants.ALL_INTENTS.
            Falls back to INTENT_UNKNOWN if classification fails.
        """
        logger.info("Classifying intent for query: %r", user_query[:80])

        try:
            raw_label = call_llm_simple(
                system_prompt=INTENT_SYSTEM_PROMPT,
                user_message=build_intent_prompt(user_query),
            )
        except RuntimeError as exc:
            logger.warning("Intent classification LLM call failed: %s", exc)
            return INTENT_UNKNOWN

        # Normalise whitespace and case
        label = raw_label.strip().lower().replace(" ", "_")

        if label in ALL_INTENTS:
            logger.info("Detected intent: %s", label)
            return label

        # The LLM occasionally returns a close variant; try a prefix match
        for known in ALL_INTENTS:
            if label.startswith(known) or known.startswith(label):
                logger.info("Intent fuzzy-matched %r → %s", label, known)
                return known

        logger.warning("Unknown intent label from LLM: %r — defaulting to unknown", label)
        return INTENT_UNKNOWN


# Module-level convenience instance
intent_service = IntentService()
