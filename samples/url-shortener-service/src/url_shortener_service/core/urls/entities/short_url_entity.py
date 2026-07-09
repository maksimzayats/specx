from dataclasses import dataclass

from specx.core.foundation.entity import BaseEntity


@dataclass(frozen=True, kw_only=True, slots=True)
class ShortUrlEntity(BaseEntity):
    """Framework-free short URL state used inside the URL scope.

    Example:
        ShortUrlEntity(id=1, code="abc123", target_url="https://example.com/docs")
    """

    id: int
    code: str
    target_url: str
