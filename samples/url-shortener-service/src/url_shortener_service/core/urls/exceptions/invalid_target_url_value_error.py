from specx.core.foundation.exceptions import BaseApplicationValueError


class InvalidTargetUrlValueError(BaseApplicationValueError):
    """Raised when a target URL cannot be shortened.

    Example:
        raise InvalidTargetUrlValueError(target_url="ftp://example.com")
    """

    def __init__(self, *, target_url: str) -> None:
        super().__init__(f"Invalid target URL: {target_url!r}")
        self.target_url = target_url
