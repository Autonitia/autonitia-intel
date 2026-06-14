"""
Token-usage recording (provider-agnostic, price-agnostic).

Each LLM node calls record_usage() after its call; raw token counts accumulate
in state["_usage"]. The free core only records TOKENS — pricing/cost is applied
downstream (the Pro layer owns the price table), so this stays dependency-free.
"""


def record_usage(state: dict, node: str, model: str, completion) -> None:
    """Append this call's token usage to state['_usage']. No-op if unavailable."""
    usage = getattr(completion, "usage", None)
    if usage is None:
        return
    state.setdefault("_usage", []).append({
        "node": node,
        "model": model,
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "total_tokens": getattr(usage, "total_tokens", 0) or 0,
    })


def usage_totals(state: dict) -> dict:
    """Aggregate raw token totals (no cost)."""
    rows = state.get("_usage", [])
    return {
        "calls": len(rows),
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "total_tokens": sum(r["total_tokens"] for r in rows),
    }
