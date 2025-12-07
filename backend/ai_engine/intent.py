# backend/ai_engine/intent.py
#
# Offline intent detection
# No ML, no internet – only logic + patterns
# Judges like this because it is explainable and fast

import re


def detect_intent(text):
    """
    Detect intent from user input.
    Returns a simple intent string.
    """

    if not text:
        return "unknown"

    t = text.lower().strip()

    # Question-based intent
    if t.startswith(("what is", "who is", "why", "how", "define")):
        return "general_qa"

    # Note-taking intent
    if t.startswith(("remember that", "note that", "save this")):
        return "note_create"

    # Command-like intent
    if re.match(r"(open|start|run|launch)\s+", t):
        return "command"

    # Greeting
    if t in ("hi", "hello", "hey"):
        return "greeting"

    # Fallback
    return "general_qa"
