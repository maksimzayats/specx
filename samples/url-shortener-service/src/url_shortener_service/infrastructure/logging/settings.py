from typing import ClassVar

from pydantic_settings import SettingsConfigDict
from specx.core.foundation.enums import BaseStrEnum
from specx.infrastructure.foundation.settings import BaseRuntimeSettings


class LogLevelEnum(BaseStrEnum):
    """Supported runtime logging levels.

    Example:
        LogLevelEnum.INFO
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingSettings(BaseRuntimeSettings):
    """Settings for process-wide Python logging configuration.

    Example:
        LoggingSettings(level=LogLevelEnum.INFO)
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="LOGGING_",
        env_file=".env",
        extra="ignore",
    )

    level: LogLevelEnum = LogLevelEnum.INFO
    message_format: str = "%(asctime)s %(levelname)s %(name)s %(message)s"
    date_format: str = "%Y-%m-%dT%H:%M:%S%z"
