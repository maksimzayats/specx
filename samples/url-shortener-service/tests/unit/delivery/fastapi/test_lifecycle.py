from __future__ import annotations

from dataclasses import dataclass

import pytest
from diwire import Container
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from url_shortener_service.delivery.fastapi.lifecycle import FastAPILifecycle
from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from url_shortener_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@dataclass(kw_only=True, slots=True)
class ClosableSQLAlchemySessionFactory(SQLAlchemySessionFactory):
    """Session factory double that records lifecycle close calls.

    Example:
        factory = ClosableSQLAlchemySessionFactory(_settings=settings)
    """

    events: list[str]

    def __post_init__(self) -> None:
        pass

    def __call__(self) -> async_sessionmaker[AsyncSession]:
        raise AssertionError("Lifecycle tests should not open sessions.")

    async def close(self) -> None:
        self.events.append("sqlalchemy.close")


@pytest.mark.anyio
async def test_lifespan_closes_sqlalchemy_before_container(
    container: Container,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    session_factory = ClosableSQLAlchemySessionFactory(
        _settings=DatabaseSettings(database_url="sqlite+aiosqlite:///lifecycle.sqlite3"),
        events=events,
    )

    async def record_container_close() -> None:
        events.append("container.aclose")

    monkeypatch.setattr(container, "aclose", record_container_close)
    container.add_instance(container, provides=Container)
    container.add_instance(session_factory, provides=SQLAlchemySessionFactory)

    lifecycle = container.resolve(FastAPILifecycle)

    async with lifecycle(FastAPI()):
        events.append("lifespan.open")

    assert events == [
        "lifespan.open",
        "sqlalchemy.close",
        "container.aclose",
    ]


@pytest.mark.anyio
async def test_lifespan_closes_resources_when_app_scope_raises(
    container: Container,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    session_factory = ClosableSQLAlchemySessionFactory(
        _settings=DatabaseSettings(database_url="sqlite+aiosqlite:///lifecycle.sqlite3"),
        events=events,
    )

    async def record_container_close() -> None:
        events.append("container.aclose")

    monkeypatch.setattr(container, "aclose", record_container_close)
    container.add_instance(container, provides=Container)
    container.add_instance(session_factory, provides=SQLAlchemySessionFactory)

    lifecycle = container.resolve(FastAPILifecycle)

    with pytest.raises(RuntimeError, match="request handling failed"):
        async with lifecycle(FastAPI()):
            raise RuntimeError("request handling failed")

    assert events == [
        "sqlalchemy.close",
        "container.aclose",
    ]
