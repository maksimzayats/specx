from specx.core.foundation.exceptions import BaseApplicationError


class ShortUrlNotFoundError(BaseApplicationError):
    """Raised when a short code has no stored target URL.

    Example:
        raise ShortUrlNotFoundError(code="abc123")
    """

    def __init__(self, *, code: str) -> None:
        super().__init__(f"Short URL not found: {code}")
        self.code = code
