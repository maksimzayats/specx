from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from specx.core.foundation.pure_service import BasePureService

from url_shortener_service.core.urls.exceptions.invalid_target_url_value_error import (
    InvalidTargetUrlValueError,
)


@dataclass(kw_only=True, slots=True)
class TargetUrlNormalizerService(BasePureService):
    """Service that normalizes and validates target URLs before persistence.

    Example:
        normalizer.normalize(target_url=" HTTPS://Example.COM/docs#top ")
    """

    def normalize(self, *, target_url: str) -> str:
        stripped = target_url.strip()
        parsed = urlsplit(stripped)

        scheme = parsed.scheme.lower()
        if scheme not in {"http", "https"} or parsed.hostname is None:
            raise InvalidTargetUrlValueError(target_url=target_url)

        hostname = parsed.hostname.lower()
        port = f":{parsed.port}" if parsed.port is not None else ""
        netloc = f"{hostname}{port}"
        path = parsed.path or ""

        return urlunsplit((scheme, netloc, path, parsed.query, ""))
