"""FastAPI Application entrypoint for AgentPulse."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agentpulse.core.errors import (
    AgentPulseError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from agentpulse.core.settings import get_settings


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    """Readiness check payload."""

    status: str
    checks: dict[str, str]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan context."""
    # Lifecycle startup hooks
    yield
    # Lifecycle shutdown hooks


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AgentPulse API",
        version="0.1.0",
        description="Observability, evaluation, and guardrails for conversational AI and RAG",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global domain exception handlers
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(_request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(AuthorizationError)
    async def forbidden_handler(_request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(AgentPulseError)
    async def domain_error_handler(_request: Request, exc: AgentPulseError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.get("/healthz", response_model=HealthResponse, tags=["Health"])
    async def healthz() -> HealthResponse:
        """Liveness health check."""
        return HealthResponse(
            status="ok",
            version="0.1.0",
            environment=settings.environment,
        )

    @app.get("/readyz", response_model=ReadyResponse, tags=["Health"])
    async def readyz() -> ReadyResponse:
        """Readiness check verifying backend readiness."""
        checks: dict[str, str] = {
            "api": "ok",
        }
        return ReadyResponse(
            status="ok",
            checks=checks,
        )

    return app


app = create_app()
