from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal

from tests.unit.core.urls.repositories.fake_short_url_repository import (
    InMemoryShortUrlRepository,
)
from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity
from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
    ShortUrlUnitOfWorkManager,
)


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWork(ShortUrlUnitOfWork):
    """Active in-memory UoW for URL unit tests.

    Example:
        unit_of_work = InMemoryShortUrlUnitOfWork(_short_urls=repository)
    """

    _short_urls: ShortUrlRepository

    @property
    def short_urls(self) -> ShortUrlRepository:
        return self._short_urls


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWorkManager(ShortUrlUnitOfWorkManager):
    """In-memory UoW manager double for URL unit tests.

    Example:
        async with manager as unit_of_work:
            await unit_of_work.short_urls.find_by_code(code="abc1234")
    """

    repository: InMemoryShortUrlRepository = field(default_factory=InMemoryShortUrlRepository)
    entered_count: int = 0
    committed_count: int = 0
    rolled_back_count: int = 0
    _snapshot: tuple[dict[str, ShortUrlEntity], int] = field(
        default_factory=lambda: ({}, 1),
        init=False,
    )

    async def __aenter__(self) -> ShortUrlUnitOfWork:
        self.entered_count += 1
        self._snapshot = self.repository.snapshot()

        return InMemoryShortUrlUnitOfWork(_short_urls=self.repository)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        _ = exc
        _ = traceback
        if exc_type is None:
            self.committed_count += 1
        else:
            self.repository.restore(self._snapshot)
            self.rolled_back_count += 1

        return False
