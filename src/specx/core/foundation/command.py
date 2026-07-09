from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class BaseCommand:
    """Base for use-case inputs that request state-changing work.

    Commands are input contracts and do not inherit `BaseDTO`.

    Example:
        from dataclasses import dataclass

        @dataclass(frozen=True, kw_only=True, slots=True)
        class CreateTaskCommand(BaseCommand):
            title: str
    """
