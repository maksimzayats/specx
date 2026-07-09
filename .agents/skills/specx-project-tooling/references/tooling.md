# Specx Tooling Reference

Use this for a new Python 3.14 service. Preserve existing versions in existing
repos unless the user asks to change them.

## Minimal `pyproject.toml`

Replace `order-service` and `order_service`.

```toml
[project]
name = "order-service"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "diwire>=1.4.2",
    "fastapi>=0.138.0",
    "pydantic-settings>=2.14.0",
    "pydantic>=2.13.0",
    "specx>=0.1.0",
    "uvicorn[standard]>=0.49.0",
]

[dependency-groups]
dev = [
    "httpx2>=0.28.0",
    "mypy>=2.1.0",
    "pytest>=9.1.0",
    "pytest-cov>=7.1.0",
    "ruff>=0.15.0",
]

[build-system]
requires = ["uv_build>=0.11.0,<0.12.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "order_service"

[tool.mypy]
python_version = "3.14"
strict = true
plugins = ["diwire.integrations.mypy_plugin"]
warn_unreachable = true
extra_checks = true

[tool.pytest.ini_options]
minversion = "9.0"
addopts = "-vv --strict-config --strict-markers --import-mode=importlib"
pythonpath = ["."]
testpaths = ["tests"]
xfail_strict = true

[tool.ruff]
target-version = "py314"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "A",
    "ASYNC",
    "B",
    "C4",
    "E",
    "F",
    "I",
    "N",
    "PIE",
    "PT",
    "PTH",
    "RET",
    "RUF",
    "SIM",
    "UP",
]
ignore = []
```

## Minimal Makefile

Replace `order_service.delivery.fastapi.__main__:app`.

```makefile
.PHONY: check dev format lint test

dev:
	uv run uvicorn order_service.delivery.fastapi.__main__:app --reload --host 0.0.0.0 --port 8000

check: lint test

format:
	uv run ruff check --fix .
	uv run ruff format .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

test:
	uv run pytest
```

## SQL Adapter Additions

When a SQLAlchemy adapter exists, add the runtime dependencies and Makefile
targets from `$specx-sqlalchemy-migrations`:

```toml
dependencies = [
    "aiosqlite>=0.22.0",
    "alembic>=1.16.0",
    "sqlalchemy[asyncio]>=2.0.0",
]
```

```makefile
.PHONY: makemigrations migrate migration-check

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
```

## Dependency Choices

- Add `sqlalchemy[asyncio]`, `alembic`, and a DB driver only when a SQL adapter
  exists. Once a SQLAlchemy adapter exists, Alembic config, migration commands,
  and migration tests are required.
- Add `redis` only when a Redis adapter exists.
- Add `httpx` as runtime only when production code performs outbound HTTP.
- Use `httpx2` in dev when route tests need in-process ASGI clients. Prefer
  `AsyncClient` with `ASGITransport` for FastAPI integration tests.
- Add `specx` as a runtime dependency when generated projects import packaged
  foundation bases. The standard architecture wrapper in `tests/guardrails`
  uses the same package.

## Validation

Run these after creating the project:

```bash
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy .
uv run pytest
```

## AGENTS.md Commands

Keep root `AGENTS.md` aligned with the actual Makefile. For the standard FastAPI
project, include:

```markdown
- Install: `uv sync --all-groups`
- Dev server: `make dev`
- Full check: `make check`
- Lint/type/format check: `make lint`
- Format/fix: `make format`
- Tests: `make test`
- Targeted unit tests: `uv run pytest tests/unit`
- Targeted integration tests: `uv run pytest tests/integration`
- Targeted guardrail tests: `uv run pytest tests/guardrails`
```

When SQLAlchemy/Alembic exists, also include:

```markdown
- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`
```

Do not list commands that do not exist in that project.
