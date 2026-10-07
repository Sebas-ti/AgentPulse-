"""User session authentication for query API."""

import uuid
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agentpulse.auth.api_key import DEV_PROJECT_ID, get_or_create_dev_context
from agentpulse.core.settings import Settings, get_settings
from agentpulse.db.session import get_db_session


@dataclass(frozen=True)
class UserContext:
    """Security context for query/read operations."""

    project_id: uuid.UUID
    role: str = "admin"


async def get_current_user_context(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> UserContext:
    """Dependency for authenticated user session.

    Uses dev provider until Phase 6 (Entra ID).
    """
    if settings.auth_provider == "dev":
        await get_or_create_dev_context(session, "qa")
        return UserContext(project_id=DEV_PROJECT_ID, role="admin")

    # In production with Entra ID (Phase 6), extracts claims from JWT
    return UserContext(project_id=DEV_PROJECT_ID, role="admin")
