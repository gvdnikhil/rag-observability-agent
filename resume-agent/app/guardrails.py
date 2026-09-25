import os

# Short, keyword-heavy resume fragments embed weaker against natural-language queries than
# full prose does (all-MiniLM-L6-v2 scores clearly-on-topic resume chunks as low as ~0.15-0.25
# in testing), so this service's default is lower than a prose-corpus guardrail would use.
# Configurable so it can be tuned without a code change.
SIMILARITY_THRESHOLD = float(os.environ.get("GUARDRAIL_SIMILARITY_THRESHOLD", "0.15"))

NO_RETRIEVAL_MESSAGE = (
    "I don't have grounded information in my knowledge base to answer that — "
    "I didn't search for anything relevant before answering."
)
LOW_CONFIDENCE_MESSAGE = (
    "I couldn't find anything in my knowledge base relevant enough to answer that confidently, "
    "so I won't guess."
)


def check(trace: dict) -> dict:
    """Refuse to answer instead of letting the model hallucinate when retrieval
    didn't happen or came back weak. Same idea as GuardrailsAI-style output
    validation, without the extra dependency for this MVP.
    """
    retrieved = trace.get("retrieved", [])
    if not retrieved:
        return {
            "blocked": True,
            "reason": "no_retrieval",
            "message": NO_RETRIEVAL_MESSAGE,
            "threshold": SIMILARITY_THRESHOLD,
        }

    best_score = max(r["score"] for r in retrieved)
    if best_score < SIMILARITY_THRESHOLD:
        return {
            "blocked": True,
            "reason": "low_similarity",
            "message": LOW_CONFIDENCE_MESSAGE,
            "best_score": best_score,
            "threshold": SIMILARITY_THRESHOLD,
        }

    return {
        "blocked": False,
        "reason": None,
        "message": None,
        "best_score": best_score,
        "threshold": SIMILARITY_THRESHOLD,
    }
