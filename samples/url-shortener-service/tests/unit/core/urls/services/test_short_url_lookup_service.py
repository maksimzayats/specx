from __future__ import annotations

import pytest
from diwire import Container

from tests.unit.core.urls.repositories.fake_short_url_unit_of_work import (
    InMemoryShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.exceptions.short_url_not_found_error import (
    ShortUrlNotFoundError,
)
from url_shortener_service.core.urls.services.short_url_lookup_service import (
    ShortUrlLookupService,
)


@pytest.mark.anyio
async def test_get_returns_short_url_dto(container: Container) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    existing = unit_of_work_manager.repository.add_existing(
        code="abc1234",
        target_url="https://example.com/docs",
    )
    service = container.resolve(ShortUrlLookupService)

    async with unit_of_work_manager as unit_of_work:
        result = await service.get(
            unit_of_work=unit_of_work,
            code=existing.code,
        )

    assert result.id == existing.id
    assert result.code == existing.code
    assert result.target_url == existing.target_url


@pytest.mark.anyio
async def test_resolve_returns_redirect_target(container: Container) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    existing = unit_of_work_manager.repository.add_existing(
        code="abc1234",
        target_url="https://example.com/docs",
    )
    service = container.resolve(ShortUrlLookupService)

    async with unit_of_work_manager as unit_of_work:
        result = await service.resolve(
            unit_of_work=unit_of_work,
            code=existing.code,
        )

    assert result.code == existing.code
    assert result.target_url == existing.target_url


@pytest.mark.anyio
async def test_get_raises_when_code_is_missing(container: Container) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    service = container.resolve(ShortUrlLookupService)

    async with unit_of_work_manager as unit_of_work:
        with pytest.raises(ShortUrlNotFoundError) as error:
            await service.get(
                unit_of_work=unit_of_work,
                code="missing",
            )

    assert error.value.code == "missing"
