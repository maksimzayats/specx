from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Any, cast

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import url_shortener_service.core as core_package
from url_shortener_service.foundation.sqlalchemy_model import BaseSQLAlchemyModel
from url_shortener_service.infrastructure.sqlalchemy.model_discovery import (
    load_sqlalchemy_model_modules,
)
from url_shortener_service.infrastructure.sqlalchemy.settings import DatabaseSettings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _load_model_modules() -> None:
    load_sqlalchemy_model_modules(core_package=core_package)


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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
