from dataclasses import dataclass

from specx.foundation.exceptions import BaseApplicationValueError


@dataclass(kw_only=True)
class InvalidTaskTitleValueError(BaseApplicationValueError):
    """Raised when a task title is blank after normalization.

    Example:
        raise InvalidTaskTitleValueError(title="   ")
    """

    title: str
