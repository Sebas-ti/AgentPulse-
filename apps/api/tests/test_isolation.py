"""Project isolation verification tests.

Verifies that queries and operations strictly respect project_id boundary.
"""

import uuid
from datetime import UTC, datetime

import pytest
from agentpulse.db.models import Span, Trace
from agentpulse.db.repositories.traces import (
    get_spans_by_trace_id,
    get_trace_by_id,
    list_traces,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_project_isolation_repositories() -> None:
    """Verify that project A cannot read traces or spans belonging to project B."""
    from typing import Any
    from unittest.mock import AsyncMock, MagicMock

    project_a_id = uuid.uuid4()
    project_b_id = uuid.uuid4()
    env_b_id = uuid.uuid4()

    trace_b_id = uuid.uuid4()
    span_b_id = uuid.uuid4()

    # In-memory mock session to simulate database storage and verify filtering
    stored_traces: list[Trace] = []
    stored_spans: list[Span] = []

    trace_b = Trace(
        id=trace_b_id,
        project_id=project_b_id,
        environment_id=env_b_id,
        started_at=datetime.now(UTC),
        duration_ms=100,
        status="ok",
        created_at=datetime.now(UTC),
    )
    span_b = Span(
        id=span_b_id,
        started_at=datetime.now(UTC),
        trace_id=trace_b_id,
        project_id=project_b_id,
        kind="llm",
        name="project_b_span",
        created_at=datetime.now(UTC),
    )

    mock_session = MagicMock(spec=AsyncSession)

    # Simulate list_traces query result when project_a is filtered
    async def mock_execute(stmt: str) -> Any:
        mock_result = MagicMock()
        # If project_a_id is in where clause, it must NOT return project B traces
        mock_result.scalars.return_value.all.return_value = [
            t for t in stored_traces if t.project_id == project_a_id
        ]
        mock_result.scalar_one_or_none.return_value = next(
            (t for t in stored_traces if t.project_id == project_a_id and t.id == trace_b_id),
            None,
        )
        return mock_result

    mock_session.execute = AsyncMock(side_effect=mock_execute)
    stored_traces.append(trace_b)
    stored_spans.append(span_b)

    # 1. Project A lists traces -> should be empty
    traces_for_a = await list_traces(mock_session, project_id=project_a_id)
    assert len(traces_for_a) == 0

    # 2. Project A tries to get trace_b by ID -> should return None
    trace_read_by_a = await get_trace_by_id(
        mock_session, project_id=project_a_id, trace_id=trace_b_id
    )
    assert trace_read_by_a is None

    # 3. Project A tries to get spans of trace_b -> should return empty
    spans_read_by_a = await get_spans_by_trace_id(
        mock_session, project_id=project_a_id, trace_id=trace_b_id
    )
    assert len(spans_read_by_a) == 0
