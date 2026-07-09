import logging.config
from dataclasses import dataclass
from typing import Any

from diwire import Injected
from specx.infrastructure.foundation.configurator import BaseConfigurator

from url_shortener_service.infrastructure.logging.settings import LoggingSettings


@dataclass(kw_only=True, slots=True)
class LoggingConfigurator(BaseConfigurator):
    """Configurator that applies process-wide Python logging settings.

    Example:
        configurator.configure()
    """

    _settings: Injected[LoggingSettings]

    def configure(self) -> None:
        logging.config.dictConfig(self._build_config())

    def _build_config(self) -> dict[str, Any]:
        level = self._settings.level.value

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": self._settings.message_format,
                    "datefmt": self._settings.date_format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": level,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": level,
            },
        }
