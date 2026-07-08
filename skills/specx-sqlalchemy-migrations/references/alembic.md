# Specx Alembic Reference

Use Alembic as the only schema-management path for SQLAlchemy-backed services.
Application startup may open and dispose engines, but it must not create or
mutate schema.

## Layout

```text
alembic.ini
migrations/
  env.py
  script.py.mako
  versions/
src/<package>/
  foundation/infrastructure/sqlalchemy/model.py
  infrastructure/sqlalchemy/settings.py
  infrastructure/sqlalchemy/session.py
  core/<scope>/infrastructure/sqlalchemy/models/
  core/<scope>/infrastructure/sqlalchemy/repositories/
```

App-wide engine, session factory, SQLAlchemy settings, logging, and telemetry
belong under top-level `infrastructure/`. Scope-owned ORM models and
repositories stay under `core/<scope>/infrastructure/`.

## Foundation Model Base

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseSQLAlchemyModel(DeclarativeBase):
    """Base for SQLAlchemy declarative models.

    Example:
        class TaskModel(BaseSQLAlchemyModel):
            __tablename__ = "tasks"
    """

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )
```

## Async env.py Shape

```python
from __future__ import annotations

import asyncio
from importlib import import_module
from logging.config import fileConfig
from typing import Any, cast

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from order_service.foundation.infrastructure.sqlalchemy.model import BaseSQLAlchemyModel
from order_service.infrastructure.sqlalchemy.settings import DatabaseSettings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _load_model_modules() -> None:
    for module_name in (
        "order_service.core.orders.infrastructure.sqlalchemy.models.order",
    ):
        import_module(module_name)


_load_model_modules()
target_metadata = BaseSQLAlchemyModel.metadata


def _database_url() -> str:
    return DatabaseSettings().database_url


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
```

Call `run_migrations_offline()` or `run_migrations_online()` at the bottom based
on `context.is_offline_mode()`.

## Makefile Targets

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

Do not put `migrate` behind `dev` unless the user explicitly wants local
startup to run migrations.

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
down_revision: str | None = ${repr(down_revision)}
branch_labels: Sequence[str] | None = ${repr(branch_labels)}
depends_on: Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

## Tests

Add a migration smoke test whenever SQLAlchemy models exist:

```python
def test_alembic_migrations_create_schema(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'app.sqlite3'}")

    command.upgrade(alembic_config(), "head")

    # Inspect the DB and assert expected tables plus alembic_version exist.
```

Add a drift test:

```python
def test_alembic_migrations_match_models(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'drift.sqlite3'}")
    command.upgrade(alembic_config(), "head")
    command.check(alembic_config())
```

Repository and delivery integration tests should use migrated temporary
databases. They should not call `create_all`.

## Avoid

- No `metadata.create_all` or `drop_all` in `src/`.
- No schema helpers imported by delivery app factories.
- No ORM model imports in delivery controllers.
- No app-wide SQLAlchemy session factory under one core scope.
- No unchecked autogenerated migration files.
