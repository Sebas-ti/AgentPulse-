"""Accurate cost computation for spans and traces using Decimal."""

from decimal import Decimal

ONE_MILLION = Decimal("1000000")


def compute_span_cost(
    model: str | None,
    input_tokens: int,
    output_tokens: int,
    pricing: tuple[Decimal, Decimal] | None,
) -> Decimal | None:
    """Calculate span cost in USD using Decimal.

    Returns None if model is unpriced.
    """
    if not model or pricing is None:
        return None

    input_price_per_1m, output_price_per_1m = pricing

    cost_in = (Decimal(input_tokens) / ONE_MILLION) * input_price_per_1m
    cost_out = (Decimal(output_tokens) / ONE_MILLION) * output_price_per_1m

    return round(cost_in + cost_out, 6)
