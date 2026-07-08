from dataclasses import dataclass

from specx.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class BaseQuery(BaseDTO):
    """Base for use-case inputs that request read-only results.

    Example:
        from dataclasses import dataclass

        @dataclass(frozen=True, kw_only=True, slots=True)
        class GetTaskQuery(BaseQuery):
            task_id: int
    """
