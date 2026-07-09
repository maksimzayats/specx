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
from url_shortener_service.core.urls.exceptions.short_code_collision_error import (
    ShortCodeCollisionError,
)
from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.services.short_url_creation_service import (
    ShortUrlCreationService,
)


@dataclass(kw_only=True, slots=True)
class SequencedShortCodeCapability(RandomShortCodeCapability):
    """Deterministic short-code capability for creation service tests.

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
    """In-memory repository double for creation service tests.

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

    def add_existing(self, *, code: str) -> ShortUrlEntity:
        short_url = ShortUrlEntity(
            id=self._next_id,
            code=code,
            target_url="https://example.com/existing",
        )
        self._short_urls[code] = short_url
        self._next_id += 1

        return short_url


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWork(ShortUrlUnitOfWork):
    """Active in-memory UoW for creation service tests.

    Example:
        unit_of_work = InMemoryShortUrlUnitOfWork(_short_urls=repository)
    """

    _short_urls: ShortUrlRepository

    @property
    def short_urls(self) -> ShortUrlRepository:
        return self._short_urls


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlUnitOfWorkManager(ShortUrlUnitOfWorkManager):
    """In-memory UoW manager for creation service tests.

    Example:
        async with manager as unit_of_work:
            await unit_of_work.short_urls.find_by_code(code="abc1234")
    """

    repository: InMemoryShortUrlRepository = field(default_factory=InMemoryShortUrlRepository)

    async def __aenter__(self) -> ShortUrlUnitOfWork:
        return InMemoryShortUrlUnitOfWork(_short_urls=self.repository)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        _ = exc_type
        _ = exc
        _ = traceback

        return False


@pytest.mark.anyio
async def test_create_normalizes_target_url_and_persists_short_url(
    container: Container,
) -> None:
    unit_of_work_manager = container.resolve(InMemoryShortUrlUnitOfWorkManager)
    short_code_capability = SequencedShortCodeCapability(codes=["abc1234"])
    container.add_instance(short_code_capability, provides=RandomShortCodeCapability)
    service = container.resolve(ShortUrlCreationService)

    async with unit_of_work_manager as unit_of_work:
        result = await service.create(
            unit_of_work=unit_of_work,
            target_url=" HTTPS://Example.COM/docs#top ",
        )

    stored = await unit_of_work_manager.repository.find_by_code(code="abc1234")

    assert result.code == "abc1234"
    assert result.target_url == "https://example.com/docs"
    assert stored is not None
    assert stored.id == result.id
    assert stored.code == result.code
    assert stored.target_url == result.target_url


@pytest.mark.anyio
async def test_create_retries_when_generated_code_already_exists(
    container: Container,
) -> None:
    unit_of_work_manager = container.resolve(InMemoryShortUrlUnitOfWorkManager)
    short_code_capability = SequencedShortCodeCapability(codes=["taken01", "free001"])
    container.add_instance(short_code_capability, provides=RandomShortCodeCapability)
    unit_of_work_manager.repository.add_existing(code="taken01")
    service = container.resolve(ShortUrlCreationService)

    async with unit_of_work_manager as unit_of_work:
        result = await service.create(
            unit_of_work=unit_of_work,
            target_url="https://example.com/docs",
        )

    assert result.code == "free001"
    assert short_code_capability.generated_codes == ["taken01", "free001"]


@pytest.mark.anyio
async def test_create_raises_when_all_generated_codes_collide(container: Container) -> None:
    unit_of_work_manager = container.resolve(InMemoryShortUrlUnitOfWorkManager)
    short_code_capability = SequencedShortCodeCapability(codes=["taken01"] * 5)
    container.add_instance(short_code_capability, provides=RandomShortCodeCapability)
    unit_of_work_manager.repository.add_existing(code="taken01")
    service = container.resolve(ShortUrlCreationService)

    async with unit_of_work_manager as unit_of_work:
        with pytest.raises(ShortCodeCollisionError) as error:
            await service.create(
                unit_of_work=unit_of_work,
                target_url="https://example.com/docs",
            )

    assert error.value.max_attempts == 5
