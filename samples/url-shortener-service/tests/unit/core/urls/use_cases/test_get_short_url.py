from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal

import pytest
from diwire import Container

from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity
from url_shortener_service.core.urls.exceptions.short_url_not_found_error import (
    ShortUrlNotFoundError,
)
from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.use_cases.get_short_url import (
    GetShortUrlQuery,
    GetShortUrlUseCase,
)


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlRepository(ShortUrlRepository):
    """In-memory repository double for get use-case tests.

    Example:
        repository = InMemoryShortUrlRepository()
    """

    _short_urls: dict[str, ShortUrlEntity] = field(default_factory=dict, init=False)
    _next_id: int = field(default=1, init=False)

    async def add(self, *, code: str, target_url: str) -> ShortUrlEntity:
        short_url = ShortUrlEntity(id=self._next_id, code=code, target_url=target_url)
        self._short_urls[code] = short_url
        self._next_id += 1

        return short_url

    async def find_by_code(self, *, code: str) -> ShortUrlEntity | None:
        return self._short_urls.get(code)

    def add_existing(self, *, code: str, target_url: str) -> ShortUrlEntity:
        short_url = ShortUrlEntity(id=self._next_id, code=code, target_url=target_url)
        self._short_urls[code] = short_url
        self._next_id += 1

        return short_url


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWork(ShortUrlUnitOfWork):
    """Active in-memory UoW for get use-case tests.

    Example:
        unit_of_work = InMemoryShortUrlUnitOfWork(_short_urls=repository)
    """

    _short_urls: ShortUrlRepository

    @property
    def short_urls(self) -> ShortUrlRepository:
        return self._short_urls


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWorkManager(ShortUrlUnitOfWorkManager):
    """In-memory UoW manager with counters for get use-case tests.

    Example:
        async with manager as unit_of_work:
            await unit_of_work.short_urls.find_by_code(code="abc1234")
    """

    repository: InMemoryShortUrlRepository = field(default_factory=InMemoryShortUrlRepository)
    committed_count: int = 0
    rolled_back_count: int = 0

    async def __aenter__(self) -> ShortUrlUnitOfWork:
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
            self.rolled_back_count += 1

        return False


@pytest.mark.anyio
async def test_execute_returns_existing_short_url(container: Container) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)

    existing = unit_of_work_manager.repository.add_existing(
        code="abc1234",
        target_url="https://example.com/docs",
    )
    use_case = container.resolve(GetShortUrlUseCase)

    result = await use_case.execute(query=GetShortUrlQuery(code=existing.code))

    assert result.id == existing.id
    assert result.code == existing.code
    assert result.target_url == existing.target_url
    assert unit_of_work_manager.committed_count == 1


@pytest.mark.anyio
async def test_execute_rolls_back_when_code_is_missing(container: Container) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)

    use_case = container.resolve(GetShortUrlUseCase)

    with pytest.raises(ShortUrlNotFoundError):
        await use_case.execute(query=GetShortUrlQuery(code="missing"))

    assert unit_of_work_manager.rolled_back_count == 1
