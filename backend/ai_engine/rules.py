# backend/ai_engine/rules.py
#
# Rule-based fallback answers
# Used when the assistant has no stored knowledge
# Works completely offline

import datetime

# ✅ Assistant identity (single source of truth)
ASSISTANT_NAME = "ZIA"


def fallback_answer(question, intent):
    """
    Return a simple answer if the intent matches a known rule.
    Otherwise return None.
    """

    q = question.lower()

    # Greeting
    if intent == "greeting":
        return f"Hello! I am {ASSISTANT_NAME}, ready to help even without the internet."

    # Time
    if "time" in q:
        now = datetime.datetime.now()
        return now.strftime("The current time is %H:%M.")

    # Date
    if "date" in q or "day" in q:
        today = datetime.date.today()
        return today.strftime("Today's date is %d %B %Y.")

    # ✅ Identity / Name
    if (
        "who are you" in q
        or "your name" in q
        or "what is your name" in q
        or "tell me your name" in q
    ):
        return (
            f"My name is {ASSISTANT_NAME}. "
            "I am a Zero-Internet AI Assistant. "
            "I work offline, learn locally, and sync with nearby devices."
        )

    # Capability
    if "what can you do" in q:
        return (
            "I can answer questions from my local knowledge, "
            "learn new information, and synchronize with nearby devices "
            "without using the internet."
        )

    # Unknown → let the main logic decide
    return None
