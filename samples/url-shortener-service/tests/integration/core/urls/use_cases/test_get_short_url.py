import pytest
from diwire import Container

from url_shortener_service.core.urls.exceptions.short_url_not_found_error import (
    ShortUrlNotFoundError,
)
from url_shortener_service.core.urls.use_cases.get_short_url import (
    GetShortUrlQuery,
    GetShortUrlUseCase,
)


@pytest.mark.anyio
async def test_execute_raises_for_missing_code(container: Container) -> None:
    use_case = container.resolve(GetShortUrlUseCase)

    with pytest.raises(ShortUrlNotFoundError) as error:
        await use_case.execute(query=GetShortUrlQuery(code="missing"))

    assert error.value.code == "missing"
