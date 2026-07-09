from __future__ import annotations

import pytest
from diwire import Container

from tests.unit.core.urls.repositories.fake_short_url_unit_of_work import (
    InMemoryShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.exceptions.short_url_not_found_error import (
    ShortUrlNotFoundError,
)
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.use_cases.get_short_url import (
    GetShortUrlQuery,
    GetShortUrlUseCase,
)


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
