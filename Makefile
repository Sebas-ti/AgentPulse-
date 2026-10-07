.PHONY: dev check test migrate migration seed format

dev:
	docker compose up -d --build

check:
	uv run python -m ruff check .
	uv run python -m ruff format --check .
	uv run python -m pyright
	pnpm --filter web lint
	pnpm --filter web typecheck
	uv run python -m pytest
	pnpm --filter web test

test:
	uv run python -m pytest
	pnpm --filter web test

format:
	uv run python -m ruff format .
	uv run python -m ruff check --fix .

migrate:
	@echo "Applying migrations..."
	@if [ -f apps/api/alembic.ini ]; then uv run --directory apps/api alembic upgrade head; else echo "No migrations configured yet."; fi

migration:
	@echo "Creating migration $(name)..."
	@if [ -f apps/api/alembic.ini ]; then uv run --directory apps/api alembic revision --autogenerate -m "$(name)"; else echo "No migrations configured yet."; fi

seed:
	@echo "Seeding sample project and running examples/rag-agent..."
	@echo "Seed will be fully populated in Phase 1."
