# Specx Tooling Reference

Use this for a new Python 3.14 service. Preserve existing versions in existing
repos unless the user asks to change them. The example floors below were
verified on 2026-07-10; re-check official package indexes and compatibility
notes before using them in a later new project.

`specx init <path>` is the canonical framework-neutral starting point. It uses
the same strict Ruff, mypy, pytest, uv-build, guardrail, and test
settings documented here, then runs `uv add specx diwire` and
`uv add --dev mypy pytest ruff` so uv records all initial dependency versions.
Rules requiring a technology surface become applicable only when that surface
is created. The FastAPI dependencies below are additions made only when a
FastAPI delivery app is created.

Python 3.14 is the initializer default, not a support ceiling. `--python`
accepts any syntactically valid `major.minor` value and renders matching uv,
mypy, and Ruff metadata, allowing future Python releases without changing a
Specx allowlist.

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

For a neutral project, prefer `specx init order-service`. The rendered project
starts without runtime or development dependencies, then uv selects and records
the compatible releases required by the health core, IOC scaffold, and tooling:

```toml
[project]
dependencies = []
```

```bash
uv add specx diwire
uv add --dev mypy pytest ruff
```

It emits `[tool.specx]` with `select = ["ALL"]` so all applicable built-in
rules are selected explicitly. Rules requiring absent technology surfaces are
skipped without warnings under `ALL`. The following full example shows the
FastAPI dependency extension; its FastAPI rules activate when that delivery
surface exists:

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

[tool.specx]
select = ["ALL"]

[tool.ruff]
target-version = "py314"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "COM812", # Missing trailing comma.
    "COM819", # Prohibited trailing comma.
    "D100", # Missing docstring in a public module.
    "D203", # Incorrect blank line before class.
    "D206", # Docstring tab indentation.
    "D213", # Multiline docstring summary on the second line.
    "D300", # Triple single quotes.
    "E111", # Indentation with an invalid multiple.
    "E114", # Comment indentation with an invalid multiple.
    "E117", # Over-indented code.
    "Q000", # Bad quotes in an inline string.
    "Q001", # Bad quotes in a multiline string.
    "Q002", # Bad quotes in a docstring.
    "Q003", # Avoidable escaped quote.
    "Q004", # Unnecessary escaped quote.
    "W191", # Tab indentation.
]

[tool.ruff.lint.per-file-ignores]
"**/__init__.py" = [
    "D104", # Missing docstring in a public package.
]
"tests/**/*.py" = [
    "D103", # Missing docstring in a public function.
    "S101", # Use of assert detected.
]
"src/**/use_cases/*.py" = [
    "TC001", # Typing-only first-party import.
    "TC002", # Typing-only third-party import.
]
```

Ruff's `ALL` selector adopts newly released rules on upgrade. Keep that
intentional strictness, run the complete check after dependency updates, and
keep a plain-language description of the rule beside every ignored code. The global
ignores cover file-level module docstrings and Ruff formatter compatibility;
the per-file ignores preserve Specx's empty-initializer rule, pytest's
assertion model, and DIWire's runtime annotation resolution.

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

The neutral initializer emits `check`, `format`, `lint`, and `test`. The
`lint` target includes Specx architecture guardrails. Add `dev` only with a
real runnable delivery app. The FastAPI form is shown below; replace
`order_service.delivery.fastapi.__main__:app`.

```makefile
.PHONY: check dev format lint test

dev:
	uv run --locked uvicorn order_service.delivery.fastapi.__main__:app --reload

check: lint test

format:
	uv run --locked ruff check --fix .
	uv run --locked ruff format .

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .
	uv run --locked mypy .
	uv run --locked specx check

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
  foundation bases. Run `uv run --locked specx check` as the standard
  architecture guardrail; the typed Python API remains available for custom
  rules.

## Validation

Run these after creating the project:

```bash
uv sync --all-groups
uv lock --check
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy .
uv run --locked specx check
uv run --locked pytest
```

## AGENTS.md Commands

Keep root `AGENTS.md` aligned with the actual Makefile. For the standard FastAPI
project, include:

```markdown
- Install: `uv sync --locked --all-groups`
- Dev server: `make dev`
- Full check: `make check`
- Lint/type/format/architecture check: `make lint`
- Format/fix: `make format`
- Tests: `make test`
- Targeted unit tests: `uv run --locked pytest tests/unit`
- Targeted integration tests: `uv run --locked pytest tests/integration`
```

When SQLAlchemy/Alembic exists, also include:

```markdown
- Create migration: `make makemigrations message="describe change"`
- Apply migrations: `make migrate`
- Check migration drift: `make migration-check`
```

Do not list commands that do not exist in that project.
