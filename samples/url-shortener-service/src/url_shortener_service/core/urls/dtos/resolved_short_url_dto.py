from dataclasses import dataclass

from specx.core.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class ResolvedShortUrlDTO(BaseDTO):
    """DTO returned when a short code is resolved for redirect.

    Example:
        ResolvedShortUrlDTO(code="abc123", target_url="https://example.com/docs")
    """

    code: str
    target_url: str
