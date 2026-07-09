import pytest
from diwire import Container

from url_shortener_service.core.urls.use_cases.create_short_url import (
    CreateShortUrlCommand,
    CreateShortUrlUseCase,
)
from url_shortener_service.core.urls.use_cases.resolve_short_url import (
    ResolveShortUrlQuery,
    ResolveShortUrlUseCase,
)


@pytest.mark.anyio
async def test_execute_resolves_target_url(container: Container) -> None:
    create_use_case = container.resolve(CreateShortUrlUseCase)
    resolve_use_case = container.resolve(ResolveShortUrlUseCase)

    created = await create_use_case.execute(
        command=CreateShortUrlCommand(target_url="https://example.com/docs"),
    )
    resolved = await resolve_use_case.execute(
        query=ResolveShortUrlQuery(code=created.code),
    )

    assert resolved.code == created.code
    assert resolved.target_url == created.target_url
