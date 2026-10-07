"""Ingestion endpoints for OTLP and internal trace batches."""

import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentpulse.auth.api_key import IngestAuthContext, get_ingest_auth
from agentpulse.core.settings import Settings, get_settings
from agentpulse.db.models import Span, Trace
from agentpulse.db.repositories.pricing import get_pricing_for_model
from agentpulse.db.repositories.traces import save_trace_with_spans, update_trace_feedback
from agentpulse.db.session import get_db_session
from agentpulse.ingest.cost import compute_span_cost
from agentpulse.ingest.normalize import normalize_otlp_payload
from agentpulse.ingest.queue import publish_trace_ingested
from agentpulse.ingest.redact import redact_data
from agentpulse.ingest.schemas import (
    BatchIngestRequest,
    BatchIngestResponse,
    FeedbackRequest,
    TraceIngest,
)

router = APIRouter(prefix="/v1", tags=["Ingest"])


async def process_and_persist_traces(
    session: AsyncSession,
    auth: IngestAuthContext,
    traces: list[TraceIngest],
) -> list[uuid.UUID]:
    """Process, redact, calculate cost, persist traces and enqueue jobs."""
    accepted_ids: list[uuid.UUID] = []

    for t_item in traces:
        spans_models: list[Span] = []
        total_trace_cost: Decimal | None = Decimal("0") if t_item.spans else None

        for s_item in t_item.spans:
            # PII redaction
            input_val = redact_data(s_item.input) if auth.store_content else None
            output_val = redact_data(s_item.output) if auth.store_content else None
            attributes_val = redact_data(s_item.attributes)

            # Pricing lookup and cost calculation
            pricing = None
            if s_item.model:
                pricing = await get_pricing_for_model(
                    session=session,
                    model=s_item.model,
                    at_datetime=s_item.started_at,
                )

            span_cost = compute_span_cost(
                model=s_item.model,
                input_tokens=s_item.input_tokens,
                output_tokens=s_item.output_tokens,
                pricing=pricing,
            )

            if span_cost is not None and total_trace_cost is not None:
                total_trace_cost += span_cost
            elif span_cost is None:
                # If any model has missing price, trace cost is None (unpriced notice)
                total_trace_cost = None

            span_record = Span(
                id=s_item.id,
                started_at=s_item.started_at,
                trace_id=t_item.id,
                project_id=auth.project_id,
                parent_span_id=s_item.parent_span_id,
                kind=s_item.kind,
                name=s_item.name,
                duration_ms=s_item.duration_ms,
                provider=s_item.provider,
                model=s_item.model,
                input_tokens=s_item.input_tokens,
                output_tokens=s_item.output_tokens,
                cost_usd=span_cost,
                input=input_val,
                output=output_val,
                attributes=attributes_val if isinstance(attributes_val, dict) else {},
                created_at=s_item.started_at,
            )
            spans_models.append(span_record)

        trace_record = Trace(
            id=t_item.id,
            project_id=auth.project_id,
            environment_id=auth.environment_id,
            agent_version_id=None,
            session_id=t_item.session_id,
            started_at=t_item.started_at,
            duration_ms=t_item.duration_ms,
            status=t_item.status,
            input_tokens=t_item.input_tokens,
            output_tokens=t_item.output_tokens,
            cost_usd=total_trace_cost,
            created_at=t_item.started_at,
        )

        await save_trace_with_spans(
            session=session,
            trace=trace_record,
            spans=spans_models,
        )

        # Publish to stream
        await publish_trace_ingested(
            project_id=auth.project_id,
            environment_name=auth.environment_name,
            trace_id=t_item.id,
        )

        accepted_ids.append(t_item.id)

    return accepted_ids


@router.post(
    "/traces",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BatchIngestResponse,
)
async def ingest_traces_batch(
    payload: BatchIngestRequest,
    auth: IngestAuthContext = Depends(get_ingest_auth),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> BatchIngestResponse:
    """Ingest a batch of traces in internal JSON format."""
    if len(payload.traces) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Batch size {len(payload.traces)} exceeds maximum of {settings.max_batch_size}",
        )

    accepted = await process_and_persist_traces(
        session=session,
        auth=auth,
        traces=payload.traces,
    )

    return BatchIngestResponse(
        accepted_traces=accepted,
        count=len(accepted),
        environment=auth.environment_name,
    )


@router.post(
    "/otlp/v1/traces",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=BatchIngestResponse,
)
async def ingest_otlp_traces(
    request: Request,
    auth: IngestAuthContext = Depends(get_ingest_auth),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> BatchIngestResponse:
    """Ingest traces formatted according to OTLP/HTTP JSON."""
    try:
        body: Any = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload in OTLP request",
        ) from exc

    if not isinstance(body, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must be a JSON object",
        )

    payload_dict: dict[str, Any] = {str(k): v for k, v in body.items()}  # type: ignore[reportUnknownVariableType]
    traces = normalize_otlp_payload(payload_dict)

    if len(traces) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Batch size {len(traces)} exceeds maximum of {settings.max_batch_size}",
        )

    accepted = await process_and_persist_traces(
        session=session,
        auth=auth,
        traces=traces,
    )

    return BatchIngestResponse(
        accepted_traces=accepted,
        count=len(accepted),
        environment=auth.environment_name,
    )


@router.post(
    "/traces/{trace_id}/feedback",
    status_code=status.HTTP_200_OK,
)
async def submit_trace_feedback(
    trace_id: uuid.UUID,
    payload: FeedbackRequest,
    auth: IngestAuthContext = Depends(get_ingest_auth),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    """Submit end-user feedback rating for a specific trace."""
    updated = await update_trace_feedback(
        session=session,
        project_id=auth.project_id,
        trace_id=trace_id,
        feedback=payload.rating,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace {trace_id} not found in current project",
        )
    return {"status": "ok", "message": "Feedback recorded"}
