"""Pytest fixtures and test doubles for AgentPulse API testing."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest
from agentpulse.auth.api_key import DEV_PROD_ENV_ID, DEV_PROJECT_ID, DEV_QA_ENV_ID
from agentpulse.db.models import Environment, Project, Span, Trace
from agentpulse.db.session import get_db_session
from agentpulse.main import create_app
from sqlalchemy.ext.asyncio import AsyncSession


class InMemoryAsyncSession:
    """Mock in-memory session for HTTP unit tests when live Postgres is unreachable."""

    def __init__(self) -> None:
        self.projects: dict[uuid.UUID, Project] = {
            DEV_PROJECT_ID: Project(
                id=DEV_PROJECT_ID,
                name="Default Dev Project",
                retention_days=30,
                store_content=True,
                created_at=datetime.now(UTC),
            )
        }
        self.environments: dict[uuid.UUID, Environment] = {
            DEV_QA_ENV_ID: Environment(
                id=DEV_QA_ENV_ID,
                project_id=DEV_PROJECT_ID,
                name="qa",
                created_at=datetime.now(UTC),
            ),
            DEV_PROD_ENV_ID: Environment(
                id=DEV_PROD_ENV_ID,
                project_id=DEV_PROJECT_ID,
                name="prod",
                created_at=datetime.now(UTC),
            ),
        }
        self.traces: dict[uuid.UUID, Trace] = {}
        self.spans: list[Span] = []

    async def get(self, entity: type[Any], ident: Any) -> Any:
        if entity is Project:
            return self.projects.get(ident)
        if entity is Environment:
            return self.environments.get(ident)
        if entity is Trace:
            return self.traces.get(ident)
        return None

    def add(self, obj: Any) -> None:
        if isinstance(obj, Project):
            self.projects[obj.id] = obj
        elif isinstance(obj, Environment):
            self.environments[obj.id] = obj
        elif isinstance(obj, Trace):
            self.traces[obj.id] = obj
        elif isinstance(obj, Span):
            self.spans.append(obj)

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        pass

    async def execute(self, stmt: Any) -> Any:
        # Mock execution for simple queries
        class MockResult:
            def __init__(self, data: list[Any], rowcount: int = 1) -> None:
                self._data = data
                self.rowcount = rowcount

            def scalar_one_or_none(self) -> Any:
                return self._data[0] if self._data else None

            def scalars(self) -> Any:
                class ScalarsResult:
                    def __init__(self, items: list[Any]) -> None:
                        self._items = items

                    def all(self) -> list[Any]:
                        return self._items

                return ScalarsResult(self._data)

        # Trace detail lookup
        compiled = str(stmt).lower()
        if "from traces" in compiled:
            if "where" in compiled and "traces.id =" in compiled:
                # Extract trace_id or match first trace
                matched = list(self.traces.values())
                return MockResult(matched)
            return MockResult(list(self.traces.values()))

        if "from spans" in compiled:
            return MockResult(self.spans)

        if "update traces" in compiled:
            return MockResult([], rowcount=1)

        return MockResult([])


@pytest.fixture
def fake_db_session() -> InMemoryAsyncSession:
    """Fixture providing an in-memory session."""
    return InMemoryAsyncSession()


@pytest.fixture
def test_app(fake_db_session: InMemoryAsyncSession) -> Any:
    """Fixture providing FastAPI app with overridden in-memory session."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield fake_db_session  # type: ignore

    app.dependency_overrides[get_db_session] = override_get_db
    return app
