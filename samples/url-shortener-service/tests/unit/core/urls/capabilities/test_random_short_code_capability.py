from string import ascii_letters, digits

from diwire import Container

from url_shortener_service.core.urls.capabilities.random_short_code_capability import (
    RandomShortCodeCapability,
)


def test_generate_returns_url_safe_code(container: Container) -> None:
    capability = container.resolve(RandomShortCodeCapability)

    code = capability.generate()

    assert len(code) == 7
    assert set(code) <= set(ascii_letters + digits)
