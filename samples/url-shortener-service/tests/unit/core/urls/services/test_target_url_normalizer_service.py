from dataclasses import dataclass

import pytest
from diwire import Container

from url_shortener_service.core.urls.exceptions.invalid_target_url_value_error import (
    InvalidTargetUrlValueError,
)
from url_shortener_service.core.urls.services.target_url_normalizer_service import (
    TargetUrlNormalizerService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class NormalizeTargetUrlCase:
    id: str
    raw_target_url: str
    expected_target_url: str


@pytest.mark.parametrize(
    "case",
    [
        NormalizeTargetUrlCase(
            id="trims_edges_and_lowers_host",
            raw_target_url="  HTTPS://Example.COM/docs  ",
            expected_target_url="https://example.com/docs",
        ),
        NormalizeTargetUrlCase(
            id="drops_fragment_but_keeps_query",
            raw_target_url="http://Example.com/path?a=1#section",
            expected_target_url="http://example.com/path?a=1",
        ),
    ],
    ids=lambda case: case.id,
)
def test_normalize_accepts_http_urls(
    case: NormalizeTargetUrlCase,
    container: Container,
) -> None:
    service = container.resolve(TargetUrlNormalizerService)

    result = service.normalize(target_url=case.raw_target_url)

    assert result == case.expected_target_url


@pytest.mark.parametrize(
    "target_url",
    ["", "example.com/docs", "ftp://example.com/file", "https:///missing-host"],
)
def test_normalize_rejects_unsupported_urls(
    target_url: str,
    container: Container,
) -> None:
    service = container.resolve(TargetUrlNormalizerService)

    with pytest.raises(InvalidTargetUrlValueError) as error:
        service.normalize(target_url=target_url)

    assert error.value.target_url == target_url
