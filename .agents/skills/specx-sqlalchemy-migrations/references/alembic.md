# Specx Alembic Reference

Use Alembic as the only schema-management path for SQLAlchemy-backed services.
Application startup may open and dispose engines, but it must not create or
mutate schema.

## Contents

- [Layout and dependencies](#layout)
- [Foundation model base](#foundation-model-base)
- [Model discovery](#model-discovery)
- [Async env.py](#async-envpy-shape)
- [Makefile targets](#makefile-targets)
- [Revision template and review](#scriptpymako)
- [Migration tests](#tests)
- [SQLite transaction tests](#sqlite-transaction-test-support)
- [Avoid](#avoid)

## Layout

```text
alembic.ini
migrations/
  env.py
  script.py.mako
  versions/
src/<package>/
  foundation/
    sqlalchemy_model.py
  infrastructure/sqlalchemy/settings.py
  infrastructure/sqlalchemy/session.py
  infrastructure/sqlalchemy/model_discovery.py
  core/<scope>/infrastructure/sqlalchemy/models/
  core/<scope>/infrastructure/sqlalchemy/repositories/
```

App-wide engine, session factory, SQLAlchemy settings, logging, and telemetry
belong under top-level `infrastructure/`. Scope-owned ORM models and
repositories stay under `core/<scope>/infrastructure/`.

Use these runtime dependencies for an async SQLAlchemy adapter, plus its
selected driver:

```toml
dependencies = [
    "alembic>=1.18.5",
    "sqlalchemy[asyncio]>=2.0.0",
]
```

Keep the real URL in `DatabaseSettings`, not `alembic.ini`, source code, logs,
or command output. A `SecretStr` is appropriate when credentials may be
present; the examples below assume `DatabaseSettings.url: SecretStr` with
`env_prefix="DATABASE_"`, which maps to `DATABASE_URL`, and unwrap it only while
creating an engine. `migrations/env.py` is an operational entrypoint, so it may
load `DatabaseSettings` through its typed runtime-source constructor.

## Foundation Model Base

Use a project-local SQLAlchemy declarative base for generated projects. The
base owns project-local `MetaData`, so multiple generated services never share
one global metadata object through packaged foundation bases.

Place it under `src/<package>/foundation/sqlalchemy_model.py`:

```python
from typing import ClassVar

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseSQLAlchemyModel(DeclarativeBase):
    """Project-local SQLAlchemy declarative base.

    Example:
        class OrderModel(BaseSQLAlchemyModel):
            __tablename__ = "orders"
    """

    metadata: ClassVar[MetaData] = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )
```

ORM model modules and Alembic `env.py` import this local base and set
`target_metadata` to `BaseSQLAlchemyModel.metadata`.

Because the `ck` convention uses `%(constraint_name)s`, every explicit
`CheckConstraint` must have a stable name. Also name `Boolean` or `Enum` schema
types when they emit check constraints on a supported dialect. Decide this
convention before the first revision; changing it later creates noisy or
incorrect constraint diffs.

## Model Discovery

Keep discovery in one importable application module so `env.py` and its test
cannot drift into two similar-but-different implementations:

```python
from importlib import import_module
from pkgutil import walk_packages

import order_service.core as core_package

MODEL_MODULE_MARKER = ".infrastructure.sqlalchemy.models."


def discover_sqlalchemy_model_module_names() -> frozenset[str]:
    return frozenset(
        module.name
        for module in walk_packages(
            core_package.__path__,
            prefix=f"{core_package.__name__}.",
        )
        if not module.ispkg and MODEL_MODULE_MARKER in module.name
    )


def load_sqlalchemy_models() -> None:
    for module_name in sorted(discover_sqlalchemy_model_module_names()):
        import_module(module_name)
```

Place this at
`infrastructure/sqlalchemy/model_discovery.py`. Keep package `__init__.py`
files empty and side-effect free; `walk_packages` imports packages while
recursing. Model modules should only declare mappings.

## Async env.py Shape

```python
from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Any, cast

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from order_service.foundation.sqlalchemy_model import BaseSQLAlchemyModel
from order_service.infrastructure.sqlalchemy.model_discovery import (
    load_sqlalchemy_models,
)
from order_service.infrastructure.sqlalchemy.settings import DatabaseSettings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


load_sqlalchemy_models()
target_metadata = BaseSQLAlchemyModel.metadata


def _database_url() -> str:
    settings = DatabaseSettings.from_environment()
    return settings.url.get_secret_value()


def _configuration() -> dict[str, Any]:
    section = config.get_section(config.config_ini_section)
    configuration = dict(section or {})
    configuration["sqlalchemy.url"] = _database_url()
    return configuration


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        _configuration(),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        do_run_migrations(cast(Connection, connection))
        return
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Alembic has no separate async API; its synchronous migration operations run
through `AsyncConnection.run_sync`. `NullPool` prevents a short-lived CLI
process from retaining a pool, and the `finally` guarantees async engine
disposal. The optional `config.attributes["connection"]` path accepts the
synchronous `Connection` supplied inside `run_sync` by programmatic callers.
Do not call the synchronous Alembic command API from an already-running event
loop and let this branch receive an `AsyncConnection` directly.

`render_as_batch=True` makes autogenerate emit batch blocks needed for SQLite;
Alembic executes those as ordinary alters on other backends by default. Review
`compare_server_default` results against the target dialect because default
comparison is backend-specific.

## Makefile Targets

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

The disposable-file target above is only for a SQLite-backed service. For
PostgreSQL, MySQL, or another production database, point the same upgrade and
check commands at a freshly provisioned, isolated database or schema of that
family. Never run `migration-check` against a shared development, staging, or
production database. Do not put `migrate` behind `dev` unless the user
explicitly wants local startup to run migrations.

## script.py.mako

Keep generated revision imports compatible with Ruff's import sorter:

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

The sequence-capable annotations support merge revisions and multiple branch
labels. Review every generated revision before applying it. In particular:

- Alembic reports candidate operations, not a guaranteed-correct migration;
  rename detection, data preservation, check constraints, and backend-specific
  defaults need human review.
- Sequence destructive changes safely: for example, add a nullable column,
  backfill in an explicitly designed step, then enforce non-null in a later
  compatible deployment when zero downtime matters.
- Verify upgrade SQL and constraint or index names on the target database
  family. Test downgrade only when the project promises downgrade support;
  otherwise document a forward-only recovery policy.
- Never edit, delete, or reorder a revision that may already be applied. Add a
  new corrective revision.

## Tests

Add a migration smoke test whenever SQLAlchemy models exist. This example is
for a SQLite-backed service; use an isolated database of the production family
for other services. Place it at
`tests/integration/migrations/test_alembic.py`, the architecture-guardrail
exception for migration tooling and the path assumed by `PROJECT_ROOT` below:

```python
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from order_service.infrastructure.sqlalchemy.model_discovery import (
    discover_sqlalchemy_model_module_names,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src" / "order_service"


def alembic_config() -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return config


def test_alembic_migrations_create_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app.sqlite3"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")

    command.upgrade(alembic_config(), "head")

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        with engine.connect() as connection:
            table_names = set(inspect(connection).get_table_names())
    finally:
        engine.dispose()

    assert {"alembic_version", "orders"} <= table_names
```

Add a drift test:

```python
def test_alembic_migrations_match_models(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'drift.sqlite3'}")
    command.upgrade(alembic_config(), "head")
    command.check(alembic_config())
```

Add a discovery guardrail so `alembic check` cannot pass against incomplete
metadata:

```python
def test_alembic_model_discovery_finds_every_core_model_module() -> None:
    expected = {
        "order_service." + ".".join(path.relative_to(SRC_ROOT).with_suffix("").parts)
        for path in (SRC_ROOT / "core").glob(
            "*/infrastructure/sqlalchemy/models/**/*.py"
        )
        if path.name != "__init__.py"
    }

    discovered = discover_sqlalchemy_model_module_names()

    assert discovered == expected
```

`command.check()` detects candidate upgrade operations; it is not a replacement
for the smoke test, and neither test is trustworthy unless model discovery is
complete. Migration tests use a fresh isolated database or schema because DDL
is the behavior under test. Do not wrap them in the data-test rollback harness.

Repository and delivery integration tests should use migrated databases.
Prefer one database unique to each parallel test worker plus per-test outer
transactions and SQLAlchemy savepoints when the database and driver implement
savepoints correctly. Tests for commit visibility, isolation, locking,
concurrency, or after-commit behavior need separate isolation and real commits.
Tests should not call `create_all` or `drop_all`.

## SQLite Transaction Test Support

Python 3.12 added `sqlite3.Connection.autocommit`; Python 3.11 does not have
that argument. Therefore, never pass
`connect_args={"autocommit": False}` unconditionally in a supported 3.11/3.12+
test matrix. For one aiosqlite setup that spans Python versions, use
SQLAlchemy's event-hook recipe on the test engine:

```python
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine


def configure_sqlite_test_transactions(engine: AsyncEngine) -> None:
    @event.listens_for(engine.sync_engine, "connect")
    def disable_driver_begin(
        dbapi_connection: Any,
        _connection_record: Any,
    ) -> None:
        dbapi_connection.isolation_level = None

    @event.listens_for(engine.sync_engine, "begin")
    def emit_begin(connection: Connection) -> None:
        connection.exec_driver_sql("BEGIN")
```

Call this once immediately after creating the SQLite test engine, before any
connection is opened. On Python 3.12+, `connect_args={"autocommit": False}` is
a simpler alternative for both sqlite3 and aiosqlite. Do not combine that
argument with the event-hook mode. Bind per-test sessions to the already-begun
outer connection with `join_transaction_mode="create_savepoint"`, then close
the container and sessions before rolling back and closing the outer
transaction. These are SQLite workarounds, not substitutes for testing
production-dialect behavior.

## Avoid

- No `metadata.create_all` or `drop_all` in `src/`.
- No shared packaged SQLAlchemy declarative base for generated projects. Use the
  project-local `foundation/sqlalchemy_model.py` base.
- No hard-coded ORM model module tuples or duplicated discovery algorithms;
  `env.py` and its test use the shared top-level discovery module.
- No schema helpers imported by delivery app factories.
- No ORM model imports in delivery controllers.
- No app-wide SQLAlchemy session factory under one core scope.
- No unchecked autogenerated migration files.
- No edits to revisions that may already have been applied.
- No SQLite drift database when production-dialect behavior is material.
- No unconditional SQLite `autocommit` connection argument on Python 3.11.
