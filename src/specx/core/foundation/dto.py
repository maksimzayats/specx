from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class BaseDTO:
    """Base for application payloads returned by core use cases.

    Example:
        from dataclasses import dataclass

        @dataclass(frozen=True, kw_only=True, slots=True)
        class TaskDTO(BaseDTO):
            id: int
            title: str
    """
