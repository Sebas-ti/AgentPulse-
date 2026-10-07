"""Pydantic schemas for trace and span ingestion."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class SpanIngest(BaseModel):
    """Internal span ingestion schema."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    parent_span_id: uuid.UUID | None = None
    kind: Literal["llm", "retrieval", "tool", "agent", "guardrail"] = "agent"
    name: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int = 0
    provider: str | None = None
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    input: Any = None
    output: Any = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class TraceIngest(BaseModel):
    """Internal trace ingestion schema."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agent_id: uuid.UUID | None = None
    agent_version: str | None = None
    session_id: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int = 0
    status: Literal["ok", "error"] = "ok"
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal | None = None
    spans: list[SpanIngest] = Field(default_factory=lambda: list[SpanIngest]())


class BatchIngestRequest(BaseModel):
    """Request batch containing multiple traces."""

    traces: list[TraceIngest]


class BatchIngestResponse(BaseModel):
    """Response returned upon 202 acceptance."""

    accepted_traces: list[uuid.UUID]
    count: int
    environment: str


class FeedbackRequest(BaseModel):
    """Feedback payload for trace evaluation."""

    rating: int = Field(..., ge=-1, le=1, description="Feedback rating (+1 or -1)")
    comment: str | None = None
