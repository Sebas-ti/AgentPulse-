"""Tests for AgentPulse Python SDK tracer and context managers."""

import time
from typing import Any

from agentpulse.sdk import AgentPulse, span, trace


class MockAgentPulse(AgentPulse):
    """Subclass of AgentPulse that skips network requests."""

    def send_batch(self, traces: list[dict[str, Any]]) -> None:
        pass


def test_sdk_context_managers() -> None:
    """Verify trace and span context managers produce properly structured trace data."""
    client = MockAgentPulse(api_key="ap_qa_testkey", base_url="http://mock-api")

    with client.trace(name="Test Conversation", session_id="test-session-42") as trace_ctx:
        with client.span(name="Retriever", kind="retrieval", provider="vector_db") as s1:
            time.sleep(0.01)
            s1.record_usage(input_tokens=10, output_tokens=0)
            s1.output = ["doc1", "doc2"]

        with client.span(
            name="Generator", kind="llm", model="gpt-4o-mini", provider="openai"
        ) as s2:
            time.sleep(0.01)
            s2.record_usage(input_tokens=50, output_tokens=25)
            s2.output = "Test response"

    data = trace_ctx.to_dict()
    assert data["session_id"] == "test-session-42"
    assert data["status"] == "ok"
    assert data["input_tokens"] == 60
    assert data["output_tokens"] == 25
    assert len(data["spans"]) == 2
    assert data["spans"][0]["name"] == "Retriever"
    assert data["spans"][1]["name"] == "Generator"
    assert data["spans"][1]["model"] == "gpt-4o-mini"
    client.shutdown()


def test_sdk_decorators() -> None:
    """Verify @trace and @span decorators."""

    @span(name="Inner Tool", kind="tool")
    def tool_call(x: int) -> int:
        return x * 2

    @trace(name="Outer Agent")
    def agent_call(val: int) -> int:
        return tool_call(val)

    result = agent_call(21)
    assert result == 42
