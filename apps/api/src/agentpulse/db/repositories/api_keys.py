"""Repository for API keys."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agentpulse.db.models import ApiKey, Environment, Project


async def get_active_api_key_by_hash(
    session: AsyncSession, key_hash: str
) -> tuple[ApiKey, Project, Environment] | None:
    """Lookup active API key by hash, including project and environment."""
    stmt = (
        select(ApiKey)
        .options(
            selectinload(ApiKey.environment).selectinload(Environment.project),
        )
        .where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
    )
    result = await session.execute(stmt)
    key = result.scalar_one_or_none()
    if key is None:
        return None
    return key, key.environment.project, key.environment


async def create_api_key(
    session: AsyncSession,
    project_id: uuid.UUID,
    environment_id: uuid.UUID,
    prefix: str,
    key_hash: str,
) -> ApiKey:
    """Create a new API key."""
    api_key = ApiKey(
        project_id=project_id,
        environment_id=environment_id,
        prefix=prefix,
        key_hash=key_hash,
        created_at=datetime.now(UTC),
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key
