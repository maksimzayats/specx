import pytest
from diwire import Container

from url_shortener_service.core.urls.use_cases.create_short_url import (
    CreateShortUrlCommand,
    CreateShortUrlUseCase,
)
from url_shortener_service.core.urls.use_cases.get_short_url import (
    GetShortUrlQuery,
    GetShortUrlUseCase,
)


@pytest.mark.anyio
async def test_execute_normalizes_and_persists_short_url(container: Container) -> None:
    create_use_case = container.resolve(CreateShortUrlUseCase)
    get_use_case = container.resolve(GetShortUrlUseCase)

    created = await create_use_case.execute(
        command=CreateShortUrlCommand(target_url=" HTTPS://Example.COM/docs#top "),
    )
    fetched = await get_use_case.execute(query=GetShortUrlQuery(code=created.code))

    assert len(created.code) == 7
    assert created.target_url == "https://example.com/docs"
    assert fetched == created
