# backend/ai_engine/similarity.py
#
# Lightweight text similarity for offline use
# No ML models, no internet

import re


def tokenize(text):
    """
    Convert text to a set of lowercase keywords.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return set(text.split())


def jaccard_similarity(set_a, set_b):
    """
    Jaccard similarity between two sets.
    """
    if not set_a or not set_b:
        return 0.0

    intersection = set_a & set_b
    union = set_a | set_b

    return len(intersection) / len(union)


def is_similar_enough(q1, q2, threshold=0.4):
    """
    Decide if two questions are similar enough to reuse the same answer.
    """
    tokens_1 = tokenize(q1)
    tokens_2 = tokenize(q2)

    score = jaccard_similarity(tokens_1, tokens_2)

    return score >= threshold
