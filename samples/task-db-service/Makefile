.PHONY: check dev format lint makemigrations migrate migration-check test

dev:
	uv run uvicorn task_db_service.delivery.fastapi.app:app --reload --host 0.0.0.0 --port 8000

check: lint migration-check test

format:
	uv run ruff check --fix .
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

test:
	uv run pytest

makemigrations:
	@test -n "$(message)" || (echo 'Usage: make makemigrations message="describe change"' && exit 1)
	uv run alembic revision --autogenerate -m "$(message)"
	uv run ruff check --fix migrations/versions
	uv run ruff format migrations/versions

migrate:
	uv run alembic upgrade head

migration-check:
	@tmp_db="$$(uv run python -c 'from tempfile import NamedTemporaryFile; f = NamedTemporaryFile(suffix=".sqlite3", delete=False); print(f.name); f.close()')"; \
	trap 'rm -f "$$tmp_db"' EXIT; \
	DATABASE_URL="sqlite+aiosqlite:///$$tmp_db" uv run alembic upgrade head; \
	DATABASE_URL="sqlite+aiosqlite:///$$tmp_db" uv run alembic check
