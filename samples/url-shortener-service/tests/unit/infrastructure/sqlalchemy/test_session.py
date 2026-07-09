from __future__ import annotations

from dataclasses import dataclass

import pytest
from diwire import Container

from url_shortener_service.infrastructure.sqlalchemy import session as sqlalchemy_session
from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from url_shortener_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@dataclass(kw_only=True, slots=True)
class DisposableAsyncEngine:
    """Async engine double that records dispose calls.

    Example:
        engine = DisposableAsyncEngine()
    """

    dispose_count: int = 0

    async def dispose(self) -> None:
        self.dispose_count += 1


@pytest.mark.anyio
async def test_close_disposes_engine_once(
    container: Container,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = DisposableAsyncEngine()
    settings = DatabaseSettings(database_url="sqlite+aiosqlite:///session.sqlite3")

    monkeypatch.setattr(
        sqlalchemy_session,
        "create_async_engine",
        lambda database_url: engine,
    )
    container.add_instance(settings, provides=DatabaseSettings)

    session_factory = container.resolve(SQLAlchemySessionFactory)

    await session_factory.close()
    await session_factory.close()

    assert engine.dispose_count == 1
