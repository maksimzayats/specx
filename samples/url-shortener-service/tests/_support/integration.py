from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from alembic.config import Config
from diwire import Container

from tests._support.db.sqlalchemy import (
    BoundSQLAlchemySessionFactory,
    open_transactional_session_factory,
)
from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from url_shortener_service.ioc.container import get_container


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
