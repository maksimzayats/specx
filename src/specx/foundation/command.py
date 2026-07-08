from dataclasses import dataclass

from specx.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class BaseCommand(BaseDTO):
    """Base for use-case inputs that request state-changing work.

    Example:
        from dataclasses import dataclass

        @dataclass(frozen=True, kw_only=True, slots=True)
        class CreateTaskCommand(BaseCommand):
            title: str
    """
