"""Tests for health and readiness endpoints."""

import pytest
from agentpulse.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_healthz_endpoint() -> None:
    """Verify /healthz returns status 200 with ok status."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "environment" in data


@pytest.mark.asyncio
async def test_readyz_endpoint() -> None:
    """Verify /readyz returns status 200 with checks."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/readyz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["api"] == "ok"
