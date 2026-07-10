# Specx Settings Reference

Use `pydantic-settings` for runtime configuration.

## Contents

- [Local adapter settings](#local-adapter-settings)
- [Database settings](#database-settings)
- [DIWire composition](#diwire-composition)
- [Core configuration boundary](#core-configuration-boundary)
- [Application settings](#application-settings)
- [Logging settings](#logging-settings)
- [Environment example](#envexample)
- [Tests](#tests)
- [Avoid](#avoid)

## Local Adapter Settings

Place settings near the consumer when only one class needs them:

```python
from typing import ClassVar

from pydantic import AnyHttpUrl, PositiveFloat
from pydantic_settings import SettingsConfigDict
from specx.infrastructure.foundation.settings import BaseRuntimeSettings


class UserDirectorySettings(BaseRuntimeSettings):
    """Runtime settings for the user directory HTTP adapter.

    Example:
        settings = UserDirectorySettings.model_validate(
            {
                "base_url": "https://example.invalid",
                "timeout_seconds": 5.0,
            },
        )
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="USER_DIRECTORY_",
        env_file=".env",
        env_file_encoding="utf-8",
        dotenv_filtering="match_prefix",
        extra="forbid",
    )

    base_url: AnyHttpUrl
    timeout_seconds: PositiveFloat = 5.0
```

Then inject the settings:

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.users.gateways.user_directory_gateway import (
    UserDirectoryGateway,
)


@dataclass(kw_only=True, slots=True)
class HttpUserDirectoryGateway(UserDirectoryGateway):
    """HTTP adapter for user-directory lookups.

    External effect: calls the user-directory HTTP API.

    Example:
        email = await gateway.find_email(user_id="user-1")
    """

    _settings: Injected[UserDirectorySettings]
```

`dotenv_filtering="match_prefix"` lets multiple scoped settings classes share
one `.env` file while `extra="forbid"` still catches misspelled variables that
start with this class's prefix. Pydantic resolves a relative `env_file` only
from the process working directory; it does not search parent directories.

Use `SecretStr` for tokens, passwords, and API keys. Call
`get_secret_value()` only at the infrastructure client call that needs the raw
credential; never log or interpolate the raw value.

## Database Settings

An application-scoped SQLAlchemy engine is shared technical infrastructure, so
its settings live under top-level `infrastructure/sqlalchemy/settings.py`.
Keep the environment name unambiguous: an `env_prefix="DATABASE_"` class uses
a field named `url`, producing `DATABASE_URL` rather than
`DATABASE_DATABASE_URL`.

```python
from typing import ClassVar

from pydantic import SecretStr
from pydantic_settings import SettingsConfigDict
from specx.infrastructure.foundation.settings import BaseRuntimeSettings


class DatabaseSettings(BaseRuntimeSettings):
    """Runtime settings for the application SQLAlchemy engine.

    Example:
        settings = DatabaseSettings.model_validate(
            {"url": "sqlite+aiosqlite:///./app.sqlite3"},
        )
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        dotenv_filtering="match_prefix",
        extra="forbid",
    )

    url: SecretStr
```

Use `DatabaseSettings.from_environment()` at operational entrypoints such as
Alembic. The packaged constructor isolates the unavoidable type-checking gap:
Pydantic can populate required fields from runtime sources, but a static type
checker sees only a required model field. Explicit test and composition
overrides should use `model_validate(...)` as shown above.

## DIWire Composition

DIWire auto-registers `BaseRuntimeSettings` subclasses as zero-argument,
root-scoped singleton factories. Normal consumers need only the
`Injected[UserDirectorySettings]` field shown above. For a test override, add a
prebuilt instance before resolving the consumer:

```python
settings = UserDirectorySettings.model_validate(
    {"base_url": "https://example.test"},
)
container.add_instance(settings, provides=UserDirectorySettings)
```

## Core Configuration Boundary

Runtime settings are infrastructure models. Do not inject them into core use
cases, services, capabilities, entities, repositories, or gateway ports. If a
setting controls a genuine business decision, map it at composition into a
typed core value or capability. For example, given an edge-owned
`LoginPolicySettings`:

```python
login_policy_settings = container.resolve(LoginPolicySettings)
login_policy = LoginPolicyCapability(
    maximum_failed_attempts=login_policy_settings.maximum_failed_attempts,
)
container.add_instance(login_policy, provides=LoginPolicyCapability)
```

`LoginPolicySettings` remains edge-owned. `LoginPolicyCapability` lives in core,
inherits `BaseCapability`, and has no Pydantic or settings imports. Technical
values such as HTTP timeouts and pool sizes stay in the infrastructure adapter
that consumes their settings.

## Application Settings

Use a shared settings class only for app-wide values:

```python
from typing import ClassVar

from pydantic_settings import SettingsConfigDict
from specx.core.foundation.enums import BaseStrEnum
from specx.infrastructure.foundation.settings import BaseRuntimeSettings


class EnvironmentEnum(BaseStrEnum):
    """Known runtime environments for the application.

    Example:
        EnvironmentEnum.LOCAL
    """

    LOCAL = "local"
    TEST = "test"
    PRODUCTION = "production"


class ApplicationSettings(BaseRuntimeSettings):
    """Application-wide runtime settings.

    Example:
        ApplicationSettings(environment=EnvironmentEnum.LOCAL)
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        dotenv_filtering="match_prefix",
        extra="forbid",
    )

    environment: EnvironmentEnum = EnvironmentEnum.PRODUCTION
    service_name: str = "order-service"
```

## Logging Settings

Generated API services include top-level logging settings near the logging
configurator because logging is process-wide infrastructure:

```python
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
        env_file_encoding="utf-8",
        dotenv_filtering="match_prefix",
        extra="forbid",
    )

    level: LogLevelEnum = LogLevelEnum.INFO
    message_format: str = "%(asctime)s %(levelname)s %(name)s %(message)s"
    date_format: str = "%Y-%m-%dT%H:%M:%S%z"
```

## `.env.example`

Document only values a developer may need to provide or override. Include
app-wide values such as environment and service name when the app reads them.
Include adapter-specific values only after the adapter exists. Do not add
placeholder database, Redis, or API variables for scopes that do not use
them.

```dotenv
APP_ENVIRONMENT=local
APP_SERVICE_NAME=order-service
LOGGING_LEVEL=INFO
```

Commit `.env.example`, keep `.env` out of version control, and never include
real secrets.

When adding an adapter with settings, extend `.env.example` at the same time.
For the SQLAlchemy settings above:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./app.sqlite3
```

For the user-directory adapter:

```dotenv
USER_DIRECTORY_BASE_URL=https://example.invalid
USER_DIRECTORY_TIMEOUT_SECONDS=5.0
```

## Tests

Use `monkeypatch` for runtime-source behavior and `model_validate(...)` for
explicit values. Change to an isolated working directory so a developer's
local `.env` cannot affect the test:

```python
from pathlib import Path

import pytest

from order_service.core.users.infrastructure.http.settings import UserDirectorySettings


def test_settings_reads_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("USER_DIRECTORY_BASE_URL", "https://example.test")

    settings = UserDirectorySettings.from_environment()

    assert str(settings.base_url) == "https://example.test/"
```

## Avoid

- No direct `os.environ` reads outside settings classes or composition code.
- No global settings singleton hidden in core.
- No `BaseRuntimeSettings` injection anywhere in core; map business policy to a
  typed core value or capability at composition.
- No settings objects passed through delivery request schemas.
- No broad `Settings` class for unrelated scope config.
- No direct raw `BaseSettings` inheritance; use
  `specx.infrastructure.foundation.settings.BaseRuntimeSettings`.
