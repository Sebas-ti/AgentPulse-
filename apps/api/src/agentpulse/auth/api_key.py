"""API Key authentication for ingestion endpoints."""

import hashlib
import uuid
from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from agentpulse.core.errors import AuthenticationError
from agentpulse.core.settings import Settings, get_settings
from agentpulse.db.models import Environment, Project
from agentpulse.db.repositories.api_keys import get_active_api_key_by_hash
from agentpulse.db.session import get_db_session

# Deterministic dev project and environment UUIDs for dev mode
DEV_PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEV_QA_ENV_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
DEV_PROD_ENV_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")


@dataclass(frozen=True)
class IngestAuthContext:
    """Security context extracted from ingestion API key."""

    project_id: uuid.UUID
    environment_id: uuid.UUID
    environment_name: str
    store_content: bool


def hash_api_key(raw_key: str) -> str:
    """Compute SHA-256 hash of API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def get_or_create_dev_context(session: AsyncSession, env_name: str) -> IngestAuthContext:
    """Retrieve or seed default dev context when in dev mode."""
    # Ensure project exists
    project = await session.get(Project, DEV_PROJECT_ID)
    if project is None:
        project = Project(
            id=DEV_PROJECT_ID,
            name="Default Dev Project",
            retention_days=30,
            store_content=True,
        )
        session.add(project)

        qa_env = Environment(
            id=DEV_QA_ENV_ID,
            project_id=DEV_PROJECT_ID,
            name="qa",
        )
        prod_env = Environment(
            id=DEV_PROD_ENV_ID,
            project_id=DEV_PROJECT_ID,
            name="prod",
        )
        session.add(qa_env)
        session.add(prod_env)
        await session.commit()
        await session.refresh(project)

    env_id = DEV_QA_ENV_ID if env_name == "qa" else DEV_PROD_ENV_ID
    return IngestAuthContext(
        project_id=project.id,
        environment_id=env_id,
        environment_name=env_name,
        store_content=project.store_content,
    )


async def get_ingest_auth(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> IngestAuthContext:
    """FastAPI dependency to authenticate ingestion requests via API key."""
    if not authorization or not authorization.startswith("Bearer "):
        # In dev mode, allow fallback to dev qa context if no auth provided
        if settings.auth_provider == "dev":
            return await get_or_create_dev_context(session, "qa")
        raise AuthenticationError("Missing or invalid Authorization header")

    token = authorization.removeprefix("Bearer ").strip()

    # Format must be ap_<environment>_<random>
    parts = token.split("_", 2)
    if len(parts) < 3 or parts[0] != "ap" or parts[1] not in ("qa", "prod"):
        raise AuthenticationError("API key must follow the format 'ap_<qa|prod>_<token>'")

    env_name = parts[1]

    # In dev mode with dev token prefix
    if settings.auth_provider == "dev" and token.startswith(f"ap_{env_name}_dev"):
        return await get_or_create_dev_context(session, env_name)

    key_hash = hash_api_key(token)
    match = await get_active_api_key_by_hash(session, key_hash)
    if match is None:
        # If in dev mode, create and return context
        if settings.auth_provider == "dev":
            return await get_or_create_dev_context(session, env_name)
        raise AuthenticationError("API key is invalid or revoked")

    _api_key, project, environment = match
    return IngestAuthContext(
        project_id=project.id,
        environment_id=environment.id,
        environment_name=environment.name,
        store_content=project.store_content,
    )
