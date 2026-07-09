from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class BaseQuery:
    """Base for use-case inputs that request read-only results.

    Queries are input contracts and do not inherit `BaseDTO`.

    Example:
        from dataclasses import dataclass

        @dataclass(frozen=True, kw_only=True, slots=True)
        class GetTaskQuery(BaseQuery):
            task_id: int
    """
