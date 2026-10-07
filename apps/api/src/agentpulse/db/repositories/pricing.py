"""Repository for model pricing lookup."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from agentpulse.db.models import ModelPricing

# Default fallback pricing when DB has no custom entries yet (prices per 1M tokens)
DEFAULT_PRICING: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4o": (Decimal("2.50"), Decimal("10.00")),
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "text-embedding-3-small": (Decimal("0.02"), Decimal("0.00")),
    "text-embedding-3-large": (Decimal("0.13"), Decimal("0.00")),
}


async def get_pricing_for_model(
    session: AsyncSession,
    model: str,
    at_datetime: datetime,
) -> tuple[Decimal, Decimal] | None:
    """Find the valid pricing for model at given timestamp.

    Returns tuple of (input_per_1m_usd, output_per_1m_usd) or None if unpriced.
    """
    stmt = (
        select(ModelPricing)
        .where(
            ModelPricing.model == model,
            ModelPricing.valid_from <= at_datetime,
        )
        .order_by(desc(ModelPricing.valid_from))
        .limit(1)
    )
    result = await session.execute(stmt)
    pricing = result.scalar_one_or_none()
    if pricing is not None:
        return pricing.input_per_1m_usd, pricing.output_per_1m_usd

    # Fallback to default catalog if known
    if model in DEFAULT_PRICING:
        return DEFAULT_PRICING[model]

    return None
