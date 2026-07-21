"""Cost estimation and token pricing helpers for LLM providers."""

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000},
    "gpt-4o": {"prompt": 2.50 / 1_000_000, "completion": 10.00 / 1_000_000},
    "gpt-3.5-turbo": {"prompt": 0.50 / 1_000_000, "completion": 1.50 / 1_000_000},
}
DEFAULT_PRICING: dict[str, float] = {"prompt": 0.15 / 1_000_000, "completion": 0.60 / 1_000_000}


def calculate_estimated_cost(
    model: str, prompt_tokens: int | None, completion_tokens: int | None
) -> float | None:
    """Calculate estimated cost in USD based on token counts and model pricing tables."""

    if prompt_tokens is None and completion_tokens is None:
        return None

    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    prompt_cost = (prompt_tokens or 0) * pricing["prompt"]
    completion_cost = (completion_tokens or 0) * pricing["completion"]
    return round(prompt_cost + completion_cost, 6)
