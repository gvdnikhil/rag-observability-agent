def new_trace() -> dict:
    return {"steps": [], "retrieved": [], "tool_calls": [], "guardrail": None}


def summarize(trace: dict) -> dict:
    total_latency_ms = sum(s["latency_ms"] for s in trace["steps"])
    total_tokens = sum(
        s["tokens"]["prompt_tokens"] + s["tokens"]["completion_tokens"] for s in trace["steps"]
    )
    return {
        "llm_calls": len(trace["steps"]),
        "total_latency_ms": round(total_latency_ms, 1),
        "total_tokens": total_tokens,
        "chunks_retrieved": len(trace["retrieved"]),
        "guardrail_verdict": trace["guardrail"],
    }
