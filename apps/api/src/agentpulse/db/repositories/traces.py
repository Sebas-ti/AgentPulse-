"""Repository for traces and spans with strict project isolation."""

import uuid

from sqlalchemy import desc, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from agentpulse.db.models import Environment, Span, Trace


async def save_trace_with_spans(
    session: AsyncSession,
    trace: Trace,
    spans: list[Span],
) -> None:
    """Persist trace and associated spans in a single transaction."""
    session.add(trace)
    for span in spans:
        session.add(span)
    await session.commit()


async def list_traces(
    session: AsyncSession,
    project_id: uuid.UUID,
    environment_name: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Trace]:
    """List traces filtered strictly by project_id and optional filters."""
    stmt = (
        select(Trace)
        .where(Trace.project_id == project_id)
        .order_by(desc(Trace.started_at))
        .limit(limit)
        .offset(offset)
    )

    if environment_name is not None:
        stmt = stmt.join(Environment, Environment.id == Trace.environment_id).where(
            Environment.name == environment_name
        )

    if status_filter is not None:
        stmt = stmt.where(Trace.status == status_filter)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_trace_by_id(
    session: AsyncSession,
    project_id: uuid.UUID,
    trace_id: uuid.UUID,
) -> Trace | None:
    """Retrieve single trace strictly filtered by project_id."""
    stmt = select(Trace).where(
        Trace.project_id == project_id,
        Trace.id == trace_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_spans_by_trace_id(
    session: AsyncSession,
    project_id: uuid.UUID,
    trace_id: uuid.UUID,
) -> list[Span]:
    """Retrieve spans for trace strictly filtered by project_id."""
    stmt = (
        select(Span)
        .where(
            Span.project_id == project_id,
            Span.trace_id == trace_id,
        )
        .order_by(Span.started_at)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_trace_feedback(
    session: AsyncSession,
    project_id: uuid.UUID,
    trace_id: uuid.UUID,
    feedback: int,
) -> bool:
    """Update feedback rating for a trace strictly within project_id."""
    stmt = (
        update(Trace)
        .where(
            Trace.project_id == project_id,
            Trace.id == trace_id,
        )
        .values(feedback=feedback)
    )
    result = await session.execute(stmt)
    await session.commit()
    rowcount = getattr(result, "rowcount", None)
    if rowcount is not None:
        return bool(rowcount > 0)
    if isinstance(result, CursorResult):
        return result.rowcount > 0
    return False
