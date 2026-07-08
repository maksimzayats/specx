from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from task_db_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from task_db_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@dataclass(kw_only=True, slots=True)
class BoundSQLAlchemySessionFactory(SQLAlchemySessionFactory):
    """Test session factory bound to one externally managed transaction."""

    _engine: AsyncEngine
    _session_maker: async_sessionmaker[AsyncSession]

    def __post_init__(self) -> None:
        pass


@asynccontextmanager
async def open_transactional_session_factory(
    *,
    database_url: str,
) -> AsyncIterator[BoundSQLAlchemySessionFactory]:
    engine = create_async_engine(database_url, connect_args={"autocommit": False})
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            session_maker = async_sessionmaker(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )
            try:
                yield BoundSQLAlchemySessionFactory(
                    _settings=DatabaseSettings(database_url=database_url),
                    _engine=engine,
                    _session_maker=session_maker,
                )
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()
