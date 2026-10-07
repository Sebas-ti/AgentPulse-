"""Normalization of OpenTelemetry GenAI semantic conventions to internal schemas."""

import uuid
from datetime import UTC, datetime
from typing import Any, Literal, cast

from agentpulse.ingest.schemas import SpanIngest, TraceIngest

# Supported GenAI semantic conventions version
SUPPORTED_GENAI_SEMCONV_VERSION = "0.1.0"

OPERATION_KIND_MAP: dict[str, Literal["llm", "retrieval", "tool", "agent", "guardrail"]] = {
    "chat": "llm",
    "generate": "llm",
    "embeddings": "retrieval",
    "retrieve": "retrieval",
    "execute_tool": "tool",
    "guardrail": "guardrail",
    "agent": "agent",
}


def normalize_otlp_attributes(attributes: object) -> dict[str, Any]:
    """Extract standard attributes from an OTLP attribute dict or list of key-value pairs."""
    normalized: dict[str, Any] = {}
    if isinstance(attributes, dict):
        d = cast(dict[str, object], attributes)
        for k, v in d.items():
            key_str = str(k)
            if isinstance(v, dict):
                v_dict = cast(dict[str, object], v)
                if "stringValue" in v_dict:
                    normalized[key_str] = str(v_dict["stringValue"])
                elif "intValue" in v_dict:
                    normalized[key_str] = int(str(v_dict["intValue"]))
                elif "boolValue" in v_dict:
                    normalized[key_str] = bool(v_dict["boolValue"])
                else:
                    normalized[key_str] = v_dict
            else:
                normalized[key_str] = v
    elif isinstance(attributes, list):
        items = cast(list[object], attributes)
        for item in items:
            if isinstance(item, dict):
                item_dict = cast(dict[str, object], item)
                key = str(item_dict.get("key", ""))
                val = item_dict.get("value")
                if isinstance(val, dict):
                    v_dict = cast(dict[str, object], val)
                    normalized[key] = next(iter(v_dict.values()), None)
                else:
                    normalized[key] = val
    return normalized


def normalize_otlp_span(
    otlp_span: dict[str, Any],
    trace_id: uuid.UUID,
) -> tuple[SpanIngest, dict[str, Any]]:
    """Convert an OTLP span dictionary into an internal SpanIngest and trace-level attributes."""
    raw_attrs = otlp_span.get("attributes", {})
    attrs = normalize_otlp_attributes(raw_attrs)

    # Determine kind
    operation_name = str(attrs.get("gen_ai.operation.name", "agent")).lower()
    kind: Literal["llm", "retrieval", "tool", "agent", "guardrail"] = OPERATION_KIND_MAP.get(
        operation_name, "agent"
    )

    # Provider and Model (response model wins)
    provider = attrs.get("gen_ai.provider.name")
    model = attrs.get("gen_ai.response.model") or attrs.get("gen_ai.request.model")

    # Tokens
    input_tokens = int(attrs.get("gen_ai.usage.input_tokens", 0))
    output_tokens = int(attrs.get("gen_ai.usage.output_tokens", 0))

    # Messages
    input_data = attrs.get("gen_ai.input.messages")
    output_data = attrs.get("gen_ai.output.messages")

    # Attributes
    extra_attrs: dict[str, Any] = {}
    if "agentpulse.retrieval.documents" in attrs and kind == "retrieval":
        extra_attrs["documents"] = attrs["agentpulse.retrieval.documents"]

    # Timings
    # OTLP timestamps are typically nanoseconds unix epoch
    start_time_unix_nano = otlp_span.get("startTimeUnixNano")
    end_time_unix_nano = otlp_span.get("endTimeUnixNano")

    if start_time_unix_nano:
        started_at = datetime.fromtimestamp(int(start_time_unix_nano) / 1_000_000_000, tz=UTC)
    else:
        started_at = datetime.now(UTC)

    if start_time_unix_nano and end_time_unix_nano:
        duration_ms = max(
            0,
            int((int(end_time_unix_nano) - int(start_time_unix_nano)) / 1_000_000),
        )
    else:
        duration_ms = int(otlp_span.get("durationMs", 0))

    span_id_raw = otlp_span.get("spanId")
    if span_id_raw and isinstance(span_id_raw, str) and len(span_id_raw) == 36:
        span_id = uuid.UUID(span_id_raw)
    else:
        span_id = uuid.uuid4()

    parent_span_id_raw = otlp_span.get("parentSpanId")
    parent_span_id: uuid.UUID | None = None
    if parent_span_id_raw and isinstance(parent_span_id_raw, str) and len(parent_span_id_raw) == 36:
        parent_span_id = uuid.UUID(parent_span_id_raw)

    span = SpanIngest(
        id=span_id,
        parent_span_id=parent_span_id,
        kind=kind,
        name=str(otlp_span.get("name", "span")),
        started_at=started_at,
        duration_ms=duration_ms,
        provider=str(provider) if provider else None,
        model=str(model) if model else None,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input=input_data,
        output=output_data,
        attributes=extra_attrs,
    )

    trace_attrs = {
        "session_id": attrs.get("session.id"),
        "agent_name": attrs.get("agentpulse.agent.name"),
        "agent_version": attrs.get("agentpulse.agent.version"),
    }

    return span, trace_attrs


def normalize_otlp_payload(payload: dict[str, Any]) -> list[TraceIngest]:
    """Parse standard OTLP JSON / traces payload into internal TraceIngest list."""
    raw_resource_spans = payload.get("resourceSpans")
    resource_spans: list[object] = []
    if isinstance(raw_resource_spans, list):
        resource_spans = cast(list[object], raw_resource_spans)

    grouped_by_trace: dict[str, list[dict[str, Any]]] = {}

    for r_span in resource_spans:
        if isinstance(r_span, dict):
            r_dict = cast(dict[str, object], r_span)
            raw_scope_spans = r_dict.get("scopeSpans")
            scope_spans: list[object] = []
            if isinstance(raw_scope_spans, list):
                scope_spans = cast(list[object], raw_scope_spans)

            for s_span in scope_spans:
                if isinstance(s_span, dict):
                    s_dict = cast(dict[str, object], s_span)
                    raw_spans = s_dict.get("spans")
                    spans: list[object] = []
                    if isinstance(raw_spans, list):
                        spans = cast(list[object], raw_spans)

                    for span_item in spans:
                        if isinstance(span_item, dict):
                            span_dict = cast(dict[str, Any], span_item)
                            trace_id_val = str(span_dict.get("traceId", str(uuid.uuid4())))
                            grouped_by_trace.setdefault(trace_id_val, []).append(span_dict)

    normalized_traces: list[TraceIngest] = []

    for raw_trace_id, otlp_spans in grouped_by_trace.items():
        try:
            trace_uuid = uuid.UUID(raw_trace_id) if len(raw_trace_id) == 36 else uuid.uuid4()
        except ValueError:
            trace_uuid = uuid.uuid4()

        internal_spans: list[SpanIngest] = []
        overall_trace_attrs: dict[str, Any] = {}
        total_input_tokens = 0
        total_output_tokens = 0

        for s in otlp_spans:
            internal_span, t_attrs = normalize_otlp_span(s, trace_uuid)
            internal_spans.append(internal_span)
            total_input_tokens += internal_span.input_tokens
            total_output_tokens += internal_span.output_tokens
            for k, v in t_attrs.items():
                if v is not None:
                    overall_trace_attrs[k] = v

        earliest_start = (
            min(s.started_at for s in internal_spans) if internal_spans else datetime.now(UTC)
        )
        total_duration = max((s.duration_ms for s in internal_spans), default=0)

        trace = TraceIngest(
            id=trace_uuid,
            session_id=str(overall_trace_attrs.get("session_id"))
            if overall_trace_attrs.get("session_id")
            else None,
            agent_version=str(overall_trace_attrs.get("agent_version"))
            if overall_trace_attrs.get("agent_version")
            else None,
            started_at=earliest_start,
            duration_ms=total_duration,
            status="ok",
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            spans=internal_spans,
        )
        normalized_traces.append(trace)

    return normalized_traces
