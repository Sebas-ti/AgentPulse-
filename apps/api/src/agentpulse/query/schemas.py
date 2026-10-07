"""Pydantic schemas for query endpoints and trace inspection."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class SpanView(BaseModel):
    """View model for an individual span."""

    id: uuid.UUID
    trace_id: uuid.UUID
    parent_span_id: uuid.UUID | None
    kind: str
    name: str
    started_at: datetime
    duration_ms: int
    provider: str | None
    model: str | None
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal | None
    input: Any = None
    output: Any = None
    attributes: dict[str, Any] = {}


class TraceView(BaseModel):
    """View model for a trace in list view."""

    id: uuid.UUID
    project_id: uuid.UUID
    environment_id: uuid.UUID
    session_id: str | None
    started_at: datetime
    duration_ms: int
    status: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal | None
    feedback: int | None


class TraceDetailView(BaseModel):
    """View model for a trace with full span tree."""

    trace: TraceView
    spans: list[SpanView]
