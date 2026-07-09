from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal

from diwire import Injected
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory

from .repositories.sqlalchemy_short_url_repository import SQLAlchemyShortUrlRepository


@dataclass(kw_only=True, slots=True)
class SQLAlchemyShortUrlUnitOfWork(ShortUrlUnitOfWork):
    """Active SQLAlchemy transaction for short URL repositories.

    Example:
        short_url = await unit_of_work.short_urls.find_by_code(code="abc123")
    """

    _session: AsyncSession
    _transaction: AsyncSessionTransaction
    _short_urls: ShortUrlRepository = field(init=False)
    _closed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self._short_urls = SQLAlchemyShortUrlRepository(_session=self._session)

    @property
    def short_urls(self) -> ShortUrlRepository:
        self._ensure_open()
        return self._short_urls

    async def _commit(self) -> None:
        self._ensure_open()
        await self._transaction.commit()

    async def _rollback(self) -> None:
        self._ensure_open()
        await self._transaction.rollback()

    async def _close(self) -> None:
        if self._closed:
            return

        self._closed = True
        await self._session.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Short URL unit of work is closed")


@dataclass(kw_only=True, slots=True)
class SQLAlchemyShortUrlUnitOfWorkManager(ShortUrlUnitOfWorkManager):
    """Manager that owns SQLAlchemy short URL UoW lifecycle.

    Example:
        async with manager as unit_of_work:
            short_url = await unit_of_work.short_urls.find_by_code(code="abc123")
    """

    _session_factory: Injected[SQLAlchemySessionFactory]
    _active_unit_of_work: ContextVar[SQLAlchemyShortUrlUnitOfWork | None] = field(init=False)
    _active_token: ContextVar[Token[SQLAlchemyShortUrlUnitOfWork | None] | None] = field(
        init=False,
    )

    def __post_init__(self) -> None:
        self._active_unit_of_work = ContextVar("short_url_unit_of_work", default=None)
        self._active_token = ContextVar("short_url_unit_of_work_token", default=None)

    async def __aenter__(self) -> ShortUrlUnitOfWork:
        if self._active_unit_of_work.get() is not None:
            raise RuntimeError("Nested short URL unit of work scopes are not supported")

        session = self._session_factory()()
        transaction = await session.begin()
        unit_of_work = SQLAlchemyShortUrlUnitOfWork(
            _session=session,
            _transaction=transaction,
        )
        self._active_token.set(self._active_unit_of_work.set(unit_of_work))

        return unit_of_work

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        _ = exc
        _ = traceback
        unit_of_work = self._active_unit_of_work.get()
        token = self._active_token.get()
        if unit_of_work is None or token is None:
            raise RuntimeError("Short URL unit of work manager is not active")

        try:
            if exc_type is None:
                await unit_of_work._commit()
            else:
                await unit_of_work._rollback()
        finally:
            await unit_of_work._close()
            self._active_unit_of_work.reset(token)
            self._active_token.set(None)

        return False
