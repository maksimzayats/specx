from __future__ import annotations

import pytest
from diwire import Container

from tests.unit.core.urls.repositories.fake_short_url_unit_of_work import (
    InMemoryShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.use_cases.resolve_short_url import (
    ResolveShortUrlQuery,
    ResolveShortUrlUseCase,
)


@pytest.mark.anyio
async def test_execute_returns_redirect_target(container: Container) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)

    existing = unit_of_work_manager.repository.add_existing(
        code="abc1234",
        target_url="https://example.com/docs",
    )
    use_case = container.resolve(ResolveShortUrlUseCase)

    result = await use_case.execute(
        query=ResolveShortUrlQuery(code=existing.code),
    )

    assert result.code == existing.code
    assert result.target_url == existing.target_url
