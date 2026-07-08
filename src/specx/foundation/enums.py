from enum import StrEnum


class BaseStrEnum(StrEnum):
    """Base for string enums used by settings and application values.

    Example:
        class EnvironmentEnum(BaseStrEnum):
            LOCAL = "local"
    """
