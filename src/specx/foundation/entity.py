from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class BaseEntity:
    """Base for framework-free core state.

    Example:
        from dataclasses import dataclass

        @dataclass(frozen=True, kw_only=True, slots=True)
        class TaskEntity(BaseEntity):
            id: int
            title: str
    """
