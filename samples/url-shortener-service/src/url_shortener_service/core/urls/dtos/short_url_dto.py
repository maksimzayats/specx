from dataclasses import dataclass

from specx.core.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class ShortUrlDTO(BaseDTO):
    """DTO returned by short URL use cases.

    Example:
        ShortUrlDTO(id=1, code="abc123", target_url="https://example.com/docs")
    """

    id: int
    code: str
    target_url: str
