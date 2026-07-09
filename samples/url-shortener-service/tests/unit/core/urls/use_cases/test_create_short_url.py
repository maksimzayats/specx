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
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.use_cases.create_short_url import (
    CreateShortUrlCommand,
    CreateShortUrlUseCase,
)


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
