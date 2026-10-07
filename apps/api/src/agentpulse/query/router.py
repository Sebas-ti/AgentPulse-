"""Query endpoints for traces, spans and analytics."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentpulse.auth.user import UserContext, get_current_user_context
from agentpulse.db.repositories.traces import get_spans_by_trace_id, get_trace_by_id, list_traces
from agentpulse.db.session import get_db_session
from agentpulse.query.schemas import SpanView, TraceDetailView, TraceView

router = APIRouter(prefix="/v1", tags=["Query"])


@router.get("/traces", response_model=list[TraceView])
async def get_traces(
    environment: str | None = Query(default=None, description="Filter by environment (qa, prod)"),
    status_filter: str | None = Query(
        default=None, alias="status", description="Filter by status (ok, error)"
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[TraceView]:
    """Retrieve list of traces for active project with optional filters."""
    traces = await list_traces(
        session=session,
        project_id=user.project_id,
        environment_name=environment,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    return [
        TraceView(
            id=t.id,
            project_id=t.project_id,
            environment_id=t.environment_id,
            session_id=t.session_id,
            started_at=t.started_at,
            duration_ms=t.duration_ms,
            status=t.status,
            input_tokens=t.input_tokens,
            output_tokens=t.output_tokens,
            cost_usd=t.cost_usd,
            feedback=t.feedback,
        )
        for t in traces
    ]


@router.get("/traces/{trace_id}", response_model=TraceDetailView)
async def get_trace_detail(
    trace_id: uuid.UUID,
    user: UserContext = Depends(get_current_user_context),
    session: AsyncSession = Depends(get_db_session),
) -> TraceDetailView:
    """Retrieve full trace details with its hierarchical spans."""
    trace = await get_trace_by_id(
        session=session,
        project_id=user.project_id,
        trace_id=trace_id,
    )
    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace {trace_id} not found in current project",
        )

    spans = await get_spans_by_trace_id(
        session=session,
        project_id=user.project_id,
        trace_id=trace_id,
    )

    return TraceDetailView(
        trace=TraceView(
            id=trace.id,
            project_id=trace.project_id,
            environment_id=trace.environment_id,
            session_id=trace.session_id,
            started_at=trace.started_at,
            duration_ms=trace.duration_ms,
            status=trace.status,
            input_tokens=trace.input_tokens,
            output_tokens=trace.output_tokens,
            cost_usd=trace.cost_usd,
            feedback=trace.feedback,
        ),
        spans=[
            SpanView(
                id=s.id,
                trace_id=s.trace_id,
                parent_span_id=s.parent_span_id,
                kind=s.kind,
                name=s.name,
                started_at=s.started_at,
                duration_ms=s.duration_ms,
                provider=s.provider,
                model=s.model,
                input_tokens=s.input_tokens,
                output_tokens=s.output_tokens,
                cost_usd=s.cost_usd,
                input=s.input,
                output=s.output,
                attributes=s.attributes,
            )
            for s in spans
        ],
    )
