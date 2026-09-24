SIMILARITY_THRESHOLD = 0.3

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
        return {"blocked": True, "reason": "no_retrieval", "message": NO_RETRIEVAL_MESSAGE}

    best_score = max(r["score"] for r in retrieved)
    if best_score < SIMILARITY_THRESHOLD:
        return {
            "blocked": True,
            "reason": "low_similarity",
            "message": LOW_CONFIDENCE_MESSAGE,
            "best_score": best_score,
        }

    return {"blocked": False, "reason": None, "message": None, "best_score": best_score}
