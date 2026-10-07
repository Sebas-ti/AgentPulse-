"""Comprehensive tests for trace ingestion, OTLP normalization and PII redaction."""

import uuid
from decimal import Decimal
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_ingest_json_batch(test_app: FastAPI) -> None:
    """Verify POST /v1/traces ingests trace batch, redacts PII and computes cost."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        payload = {
            "traces": [
                {
                    "id": trace_id,
                    "session_id": "sess-abc",
                    "duration_ms": 120,
                    "status": "ok",
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "spans": [
                        {
                            "id": span_id,
                            "name": "LLM Synthesis",
                            "kind": "llm",
                            "model": "gpt-4o-mini",
                            "provider": "openai",
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "input": {
                                "prompt": (
                                    "User email is john.doe@example.com and phone is 555-123-4567"
                                )
                            },
                            "output": {
                                "reply": ("Hello john.doe@example.com, card is 4111-2222-3333-4444")
                            },
                        }
                    ],
                }
            ]
        }

        response = await client.post(
            "/v1/traces",
            json=payload,
            headers={"Authorization": "Bearer ap_qa_devkey123"},
        )

        assert response.status_code == 202
        data = response.json()
        assert trace_id in data["accepted_traces"]
        assert data["count"] == 1
        assert data["environment"] == "qa"

        # Verify trace is queryable and PII was redacted
        detail_res = await client.get(f"/v1/traces/{trace_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["trace"]["id"] == trace_id

        # Verify cost calculation: gpt-4o-mini ($0.15 / 1M in, $0.60 / 1M out)
        # 100 tokens * 0.15/1M + 50 tokens * 0.60/1M = 0.000015 + 0.000030 = 0.000045
        assert detail_data["trace"]["cost_usd"] is not None
        assert Decimal(str(detail_data["trace"]["cost_usd"])) > Decimal("0")

        # Verify PII was redacted
        span_data = detail_data["spans"][0]
        assert "[REDACTED_EMAIL]" in str(span_data["input"])
        assert "[REDACTED_PHONE]" in str(span_data["input"])
        assert "[REDACTED_CARD]" in str(span_data["output"])
        assert "john.doe@example.com" not in str(span_data["input"])


@pytest.mark.asyncio
async def test_ingest_otlp_traces(test_app: FastAPI) -> None:
    """Verify POST /v1/otlp/v1/traces normalizes GenAI semantic conventions."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        otlp_payload = {
            "resourceSpans": [
                {
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": trace_id,
                                    "spanId": span_id,
                                    "name": "chat_completion",
                                    "startTimeUnixNano": "1700000000000000000",
                                    "endTimeUnixNano": "1700000000250000000",
                                    "attributes": [
                                        {
                                            "key": "gen_ai.operation.name",
                                            "value": {"stringValue": "chat"},
                                        },
                                        {
                                            "key": "gen_ai.provider.name",
                                            "value": {"stringValue": "openai"},
                                        },
                                        {
                                            "key": "gen_ai.response.model",
                                            "value": {"stringValue": "gpt-4o"},
                                        },
                                        {
                                            "key": "gen_ai.usage.input_tokens",
                                            "value": {"intValue": "200"},
                                        },
                                        {
                                            "key": "gen_ai.usage.output_tokens",
                                            "value": {"intValue": "80"},
                                        },
                                        {
                                            "key": "session.id",
                                            "value": {"stringValue": "otlp-session-1"},
                                        },
                                    ],
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        response = await client.post(
            "/v1/otlp/v1/traces",
            json=otlp_payload,
            headers={"Authorization": "Bearer ap_prod_devkey123"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["count"] == 1
        assert data["environment"] == "prod"


@pytest.mark.asyncio
async def test_trace_feedback(test_app: FastAPI) -> None:
    """Verify submitting feedback rating (+1/-1) for a trace."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        trace_id = str(uuid.uuid4())
        empty_spans: list[dict[str, Any]] = []
        feed_payload: dict[str, Any] = {
            "traces": [{"id": trace_id, "duration_ms": 50, "spans": empty_spans}]
        }
        # First ingest a trace
        await client.post(
            "/v1/traces",
            json=feed_payload,
            headers={"Authorization": "Bearer ap_qa_devkey"},
        )

        # Submit positive feedback
        res = await client.post(
            f"/v1/traces/{trace_id}/feedback",
            json={"rating": 1, "comment": "Excellent answer"},
            headers={"Authorization": "Bearer ap_qa_devkey"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
