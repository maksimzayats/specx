from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from diwire import Container

from task_db_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from task_db_service.ioc.container import get_container
from tests._support.clients.fastapi import TestAsyncClientFactory
from tests._support.db.sqlalchemy import (
    BoundSQLAlchemySessionFactory,
    open_transactional_session_factory,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return config


@pytest.fixture(scope="session")
def migrated_database_url(
    alembic_config: Config,
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[str]:
    database_path = tmp_path_factory.mktemp("database") / "integration.sqlite3"
    database_url = f"sqlite+aiosqlite:///{database_path}"
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.upgrade(alembic_config, "head")
        yield database_url
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url


@pytest.fixture
async def transactional_session_factory(
    migrated_database_url: str,
) -> AsyncIterator[BoundSQLAlchemySessionFactory]:
    async with open_transactional_session_factory(database_url=migrated_database_url) as factory:
        yield factory


@pytest.fixture
async def transactional_container(
    transactional_session_factory: BoundSQLAlchemySessionFactory,
) -> Container:
    container = get_container()
    container.add_instance(
        transactional_session_factory,
        provides=SQLAlchemySessionFactory,
    )
    return container


@pytest.fixture
def transactional_test_async_client_factory(
    transactional_container: Container,
) -> TestAsyncClientFactory:
    return TestAsyncClientFactory(_container=transactional_container)
