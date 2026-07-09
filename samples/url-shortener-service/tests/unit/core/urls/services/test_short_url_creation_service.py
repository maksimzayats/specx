from __future__ import annotations

import pytest
from diwire import Container

from tests.unit.core.urls.capabilities.fake_random_short_code_capability import (
    SequencedShortCodeCapability,
)
from tests.unit.core.urls.repositories.fake_short_url_unit_of_work import (
    InMemoryShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.capabilities.random_short_code_capability import (
    RandomShortCodeCapability,
)
from url_shortener_service.core.urls.exceptions.short_code_collision_error import (
    ShortCodeCollisionError,
)
from url_shortener_service.core.urls.services.short_url_creation_service import (
    ShortUrlCreationService,
)


@pytest.mark.anyio
async def test_create_normalizes_target_url_and_persists_short_url(
    container: Container,
) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
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
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
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
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
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
