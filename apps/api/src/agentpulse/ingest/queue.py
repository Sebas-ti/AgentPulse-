"""Redis Stream publisher for ingested traces."""

import logging
import uuid

import redis.asyncio as aioredis

from agentpulse.core.settings import get_settings

logger = logging.getLogger("agentpulse.ingest.queue")

STREAM_KEY = "traces.ingested"
_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Get singleton async redis client."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def publish_trace_ingested(
    project_id: uuid.UUID,
    environment_name: str,
    trace_id: uuid.UUID,
) -> None:
    """Publish a trace ingestion notification to Redis Streams."""
    try:
        client = get_redis_client()
        payload: dict[str, str] = {
            "project_id": str(project_id),
            "environment": environment_name,
            "trace_id": str(trace_id),
        }
        await client.xadd(STREAM_KEY, payload)  # type: ignore[reportUnknownMemberType]
    except Exception as exc:
        # Trace is already persisted safely. Log warning if Redis is down or unavailable.
        logger.warning(
            "Could not publish trace %s to Redis stream %s: %s", trace_id, STREAM_KEY, exc
        )
