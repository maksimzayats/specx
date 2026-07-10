# Specx Tooling Reference

Use this for a new Python 3.14 service. Preserve existing versions in existing
repos unless the user asks to change them. The example floors below were
verified on 2026-07-10; re-check official package indexes and compatibility
notes before using them in a later new project.

## Contents

- [Minimal pyproject.toml](#minimal-pyprojecttoml)
- [DIWire mypy plugin](#diwire-mypy-plugin)
- [Minimal Makefile](#minimal-makefile)
- [SQL adapter additions](#sql-adapter-additions)
- [Dependency choices](#dependency-choices)
- [Validation](#validation)
- [AGENTS.md commands](#agentsmd-commands)

## Minimal `pyproject.toml`

Replace `order-service` and `order_service`.

```toml
[project]
name = "order-service"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "diwire>=1.4.2",
    "fastapi>=0.139.0",
    "pydantic-settings>=2.14.2",
    "pydantic>=2.13.4",
    "specx>=0.0.0a3",
    "uvicorn[standard]>=0.51.0",
]

[dependency-groups]
dev = [
    "anyio>=4.14.1",
    "asgi-lifespan>=2.1.0",
    "httpx2>=2.5.0",
    "mypy>=2.2.0",
    "pytest>=9.1.1",
    "ruff>=0.15.20",
]

[build-system]
requires = ["uv_build>=0.11.28,<0.12.0"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "order_service"

[tool.mypy]
python_version = "3.14"
strict = true
warn_unreachable = true
extra_checks = true

[tool.pytest.ini_options]
minversion = "9.1"
addopts = "-vv --strict-config --strict-markers --import-mode=importlib"
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

`uv` installs packaged projects editable during sync, so tests should import the
installed `src/` package. Do not add the repository root or `src` through
pytest's `pythonpath`; that can mask packaging mistakes.

Add feature-specific runtime dependencies only when used. For example,
`EmailStr` requires `email-validator`, and multipart forms require
`python-multipart`.

## DIWire Mypy Plugin

The `diwire.integrations.mypy_plugin` plugin refines signatures created by
`resolver_context.inject`. Standard Specx classes use constructor fields typed
with `Injected[...]` and do not need it. Add the plugin only when preserving an
existing, intentional function-injection integration.

## Minimal Makefile

Replace `order_service.delivery.fastapi.__main__:app`.

```makefile
.PHONY: check dev format lint lock-check test

dev:
	uv run --locked uvicorn order_service.delivery.fastapi.__main__:app --reload

check: lock-check lint test

lock-check:
	uv lock --check

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy .

test:
	uv run --locked pytest
```

Uvicorn defaults to loopback (`127.0.0.1`) for local development. Bind to
`0.0.0.0` only when a container or remote development environment requires
network exposure.

## SQL Adapter Additions

When a SQLAlchemy adapter exists, add the runtime dependencies and Makefile
targets from `$specx-sqlalchemy-migrations`:

```toml
dependencies = [
    "aiosqlite>=0.22.0",
    "alembic>=1.18.5",
    "sqlalchemy[asyncio]>=2.0.0",
]
```

```makefile
.PHONY: makemigrations migrate migration-check

makemigrations:
	@test -n "$(message)" || (echo 'Usage: make makemigrations message="describe change"' && exit 1)
	uv run --locked alembic revision --autogenerate -m "$(message)"
	uv run --locked ruff check --fix migrations/versions
	uv run --locked ruff format migrations/versions

migrate:
	uv run --locked alembic upgrade head

migration-check:
	@tmp_db="$$(uv run --locked python -c 'from tempfile import NamedTemporaryFile; f = NamedTemporaryFile(suffix=".sqlite3", delete=False); print(f.name); f.close()')"; \
	trap 'rm -f "$$tmp_db"' EXIT; \
	DATABASE_URL="sqlite+aiosqlite:///$$tmp_db" uv run --locked alembic upgrade head; \
	DATABASE_URL="sqlite+aiosqlite:///$$tmp_db" uv run --locked alembic check
```

That disposable-file target is only for a SQLite-backed service. For
PostgreSQL, MySQL, or another production database, run the same upgrade and
drift check against a freshly provisioned isolated database or schema of that
family; do not use SQLite as a dialect substitute.

## Dependency Choices

- Add `sqlalchemy[asyncio]`, `alembic`, and a DB driver only when a SQL adapter
  exists. Once a SQLAlchemy adapter exists, Alembic config, migration commands,
  and migration tests are required.
- Add `redis` only when a Redis adapter exists.
- Add `httpx2` as runtime only when production code performs outbound HTTP.
- Use `httpx2` and `asgi-lifespan` in dev when route tests need in-process ASGI
  clients. HTTPX2 imports from the `httpx2` namespace. Prefer its `AsyncClient`
  with `ASGITransport`, and pass the entered lifespan manager's `manager.app`
  to the transport so lifespan state reaches requests.
- Keep `anyio` as a direct dev dependency when tests use
  `@pytest.mark.anyio`; do not rely on an incidental transitive dependency to
  provide the pytest plugin.
- Add `specx` as a runtime dependency when generated projects import packaged
  foundation bases. The standard architecture wrapper in `tests/guardrails`
  uses the same package.

## Validation

Run these after creating the project:

```bash
uv sync --all-groups
uv lock --check
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy .
uv run --locked pytest
```

## AGENTS.md Commands

Keep root `AGENTS.md` aligned with the actual Makefile. For the standard FastAPI
project, include:

```markdown
- Install: `uv sync --locked --all-groups`
- Dev server: `make dev`
- Full check: `make check`
- Verify lockfile: `make lock-check`
- Lint/type/format check: `make lint`
- Format/fix: `make format`
- Tests: `make test`
- Targeted unit tests: `uv run --locked pytest tests/unit`
- Targeted integration tests: `uv run --locked pytest tests/integration`
- Targeted guardrail tests: `uv run --locked pytest tests/guardrails`
```

When SQLAlchemy/Alembic exists, also include:

```markdown
- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`
```

Do not list commands that do not exist in that project.
