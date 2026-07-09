from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal

import pytest
from diwire import Container

from url_shortener_service.core.urls.capabilities.random_short_code_capability import (
    RandomShortCodeCapability,
)
from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity
from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.use_cases.create_short_url import (
    CreateShortUrlCommand,
    CreateShortUrlUseCase,
)


@dataclass(kw_only=True, slots=True)
class SequencedShortCodeCapability(RandomShortCodeCapability):
    """Deterministic short-code capability for create use-case tests.

    Example:
        capability = SequencedShortCodeCapability(codes=["abc1234"])
    """

    codes: list[str] = field(default_factory=list)
    generated_codes: list[str] = field(default_factory=list)

    def generate(self) -> str:
        code = self.codes.pop(0) if self.codes else super().generate()
        self.generated_codes.append(code)

        return code


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlRepository(ShortUrlRepository):
    """In-memory repository double for create use-case tests.

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


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWork(ShortUrlUnitOfWork):
    """Active in-memory UoW for create use-case tests.

    Example:
        unit_of_work = InMemoryShortUrlUnitOfWork(_short_urls=repository)
    """

    _short_urls: ShortUrlRepository

    @property
    def short_urls(self) -> ShortUrlRepository:
        return self._short_urls


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWorkManager(ShortUrlUnitOfWorkManager):
    """In-memory UoW manager with counters for create use-case tests.

    Example:
        async with manager as unit_of_work:
            await unit_of_work.short_urls.find_by_code(code="abc1234")
    """

    repository: InMemoryShortUrlRepository = field(default_factory=InMemoryShortUrlRepository)
    entered_count: int = 0
    committed_count: int = 0
    rolled_back_count: int = 0
    _snapshot_short_urls: dict[str, ShortUrlEntity] = field(default_factory=dict, init=False)
    _snapshot_next_id: int = field(default=1, init=False)

    async def __aenter__(self) -> ShortUrlUnitOfWork:
        self.entered_count += 1
        self._snapshot_short_urls = dict(self.repository._short_urls)
        self._snapshot_next_id = self.repository._next_id

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
            self.repository._short_urls = self._snapshot_short_urls
            self.repository._next_id = self._snapshot_next_id
            self.rolled_back_count += 1

        return False


@pytest.mark.anyio
async def test_execute_opens_transaction_and_creates_short_url(
    container: Container,
) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    short_code_capability = SequencedShortCodeCapability(codes=["abc1234"])

    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)
    container.add_instance(short_code_capability, provides=RandomShortCodeCapability)

    use_case = container.resolve(CreateShortUrlUseCase)

    result = await use_case.execute(
        command=CreateShortUrlCommand(target_url=" HTTPS://Example.COM/docs "),
    )

    stored = await unit_of_work_manager.repository.find_by_code(code="abc1234")

    assert result.code == "abc1234"
    assert result.target_url == "https://example.com/docs"
    assert stored is not None
    assert stored.id == result.id
    assert stored.code == result.code
    assert stored.target_url == result.target_url
    assert unit_of_work_manager.entered_count == 1
    assert unit_of_work_manager.committed_count == 1
