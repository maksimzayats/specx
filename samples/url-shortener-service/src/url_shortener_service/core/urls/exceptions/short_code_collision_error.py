from specx.core.foundation.exceptions import BaseApplicationError


class ShortCodeCollisionError(BaseApplicationError):
    """Raised when code generation cannot find an available short code.

    Example:
        raise ShortCodeCollisionError(max_attempts=5)
    """

    def __init__(self, *, max_attempts: int) -> None:
        super().__init__(f"Could not generate a unique short code after {max_attempts} attempts.")
        self.max_attempts = max_attempts
