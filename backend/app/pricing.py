"""Model pricing lookup — returns input/output cost per 1M tokens.

Prices are in USD and reflect current (mid-2026) API pricing for major providers.
Used by the AI observability cost dashboard.
"""

from __future__ import annotations

from typing import NamedTuple

ModelPrice = NamedTuple("ModelPrice", [("input_per_1m", float), ("output_per_1m", float)])

# ── Pricing data ──────────────────────────────────────────────────────

_MODEL_PRICING: dict[str, ModelPrice] = {
    # OpenAI
    "gpt-4o": ModelPrice(2.50, 10.00),
    "gpt-4o-mini": ModelPrice(0.15, 0.60),
    "gpt-4-turbo": ModelPrice(10.00, 30.00),
    "gpt-4": ModelPrice(30.00, 60.00),
    "gpt-3.5-turbo": ModelPrice(0.50, 1.50),
    "o1": ModelPrice(15.00, 60.00),
    "o1-mini": ModelPrice(1.10, 4.40),
    "o3": ModelPrice(10.00, 40.00),
    # Anthropic
    "claude-3.5-sonnet": ModelPrice(3.00, 15.00),
    "claude-3-opus": ModelPrice(15.00, 75.00),
    "claude-3-sonnet": ModelPrice(3.00, 15.00),
    "claude-3-haiku": ModelPrice(0.25, 1.25),
    "claude-4": ModelPrice(15.00, 75.00),
    "claude-4-sonnet": ModelPrice(15.00, 75.00),
    "claude-4-haiku": ModelPrice(1.00, 5.00),
    # Google
    "gemini-1.5-pro": ModelPrice(3.50, 10.50),
    "gemini-1.5-flash": ModelPrice(0.075, 0.30),
    "gemini-2.0-pro": ModelPrice(2.50, 8.00),
    "gemini-2.0-flash": ModelPrice(0.10, 0.40),
    # Mistral
    "mistral-large": ModelPrice(2.00, 6.00),
    "mistral-medium": ModelPrice(0.80, 2.40),
    "mistral-small": ModelPrice(0.20, 0.60),
    # Meta / open-weight
    "llama-3.1-405b": ModelPrice(2.75, 2.75),
    "llama-3.1-70b": ModelPrice(0.59, 0.79),
    "llama-3.1-8b": ModelPrice(0.06, 0.06),
    # Fake local (dev)
    "fake": ModelPrice(0.0, 0.0),
}


def _normalise_model(model: str) -> str:
    """Return a known key for *model* using prefix matching."""
    m = model.lower().strip()

    # Exact match first
    if m in _MODEL_PRICING:
        return m

    # Prefix matching — most specific first
    patterns = [
        "claude-3.5-sonnet",  # before claude-3
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "claude-4-haiku",
        "claude-4-sonnet",
        "claude-4",
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "gemini-2.0-pro",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "mistral-large",
        "mistral-medium",
        "mistral-small",
        "llama-3.1-405b",
        "llama-3.1-70b",
        "llama-3.1-8b",
        "o1-mini",
        "o1",
        "o3",
        "fake",
    ]
    for p in patterns:
        if p in m:
            return p
    return "gpt-4o"  # safe default


def get_model_price(model: str) -> ModelPrice:
    """Return the (input_price, output_price) per 1M tokens for *model*."""
    key = _normalise_model(model)
    return _MODEL_PRICING[key]


def compute_cost(prompt_tokens: int | None, completion_tokens: int | None, model: str) -> float:
    """Compute cost in USD from token counts and model pricing."""
    if not prompt_tokens or not completion_tokens:
        return 0.0
    input_price, output_price = get_model_price(model)
    return (prompt_tokens / 1_000_000 * input_price) + (completion_tokens / 1_000_000 * output_price)
