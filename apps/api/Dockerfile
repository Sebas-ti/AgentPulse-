FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/

# Copy workspace pyproject and api definitions
COPY pyproject.toml /app/
COPY packages/sdk-python/pyproject.toml /app/packages/sdk-python/
COPY packages/sdk-python/src /app/packages/sdk-python/src/
COPY apps/api/pyproject.toml /app/apps/api/
COPY apps/api/src /app/apps/api/src/

# Install dependencies using uv
RUN uv sync --frozen --no-dev || uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "agentpulse.main:app", "--host", "0.0.0.0", "--port", "8000"]
