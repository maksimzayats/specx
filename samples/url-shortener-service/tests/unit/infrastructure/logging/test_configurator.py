from __future__ import annotations

import logging.config
from typing import Any

import pytest
from diwire import Container

from url_shortener_service.infrastructure.logging.configurator import LoggingConfigurator
from url_shortener_service.infrastructure.logging.settings import (
    LoggingSettings,
    LogLevelEnum,
)


def test_configure_applies_readable_logging_config(
    container: Container,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_config: dict[str, Any] = {}

    def capture_dict_config(config: dict[str, Any]) -> None:
        captured_config.update(config)

    settings = LoggingSettings(
        level=LogLevelEnum.DEBUG,
        message_format="%(levelname)s %(name)s %(message)s",
        date_format="%H:%M:%S",
    )

    container.add_instance(settings, provides=LoggingSettings)
    monkeypatch.setattr(logging.config, "dictConfig", capture_dict_config)

    configurator = container.resolve(LoggingConfigurator)
    configurator.configure()

    assert captured_config["version"] == 1
    assert captured_config["disable_existing_loggers"] is False
    assert captured_config["root"] == {
        "handlers": ["console"],
        "level": "DEBUG",
    }
    assert captured_config["formatters"] == {
        "default": {
            "format": "%(levelname)s %(name)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    }
    assert captured_config["handlers"] == {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
    }
