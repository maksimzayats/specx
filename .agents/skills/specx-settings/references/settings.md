# Specx Settings Reference

Use `pydantic-settings` for runtime configuration.

## Local Adapter Settings

Place settings near the consumer when only one class needs them:

```python
from pydantic import AnyHttpUrl
from pydantic_settings import SettingsConfigDict

from specx.infrastructure.foundation.settings import BaseRuntimeSettings


class UserDirectorySettings(BaseRuntimeSettings):
    """Runtime settings for the user directory HTTP adapter.

    Example:
        UserDirectorySettings(
            base_url="https://example.invalid",
            timeout_seconds=5.0,
        )
    """

    model_config = SettingsConfigDict(
        env_prefix="USER_DIRECTORY_",
        env_file=".env",
        extra="ignore",
    )

    base_url: AnyHttpUrl
    timeout_seconds: float = 5.0
```

Then inject the settings:

```python
from dataclasses import dataclass

from diwire import Injected

from order_service.core.users.repositories.user_directory_repository import (
    UserDirectoryRepository,
)


@dataclass(kw_only=True, slots=True)
class HttpUserDirectoryRepository(UserDirectoryRepository):
    """HTTP adapter for user-directory lookups.

    Example:
        email = await repository.find_email(user_id="user-1")
    """

    _settings: Injected[UserDirectorySettings]
```

## Application Settings

Use a shared settings class only for app-wide values:

```python
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

    environment: EnvironmentEnum = EnvironmentEnum.PRODUCTION
    service_name: str = "order-service"
```

## `.env.example`

Document only values a developer may need to provide or override. Include
app-wide values such as environment and service name when the app reads them.
Include adapter-specific values only after the adapter exists. Do not add
placeholder database, Redis, or API variables for scopes that do not use
them.

```dotenv
ENVIRONMENT=local
SERVICE_NAME=order-service
```

Never include real secrets.

When adding an adapter with settings, extend `.env.example` at the same time:

```dotenv
USER_DIRECTORY_BASE_URL=https://example.invalid
USER_DIRECTORY_TIMEOUT_SECONDS=5.0
```

## Tests

Use `monkeypatch` or construct settings directly:

```python
def test_settings_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_DIRECTORY_BASE_URL", "https://example.test")

    settings = UserDirectorySettings()

    assert str(settings.base_url) == "https://example.test/"
```

## Avoid

- No direct `os.environ` reads in use cases or services.
- No global settings singleton hidden in core.
- No settings objects passed through delivery request schemas.
- No broad `Settings` class for unrelated scope config.
- No direct raw `BaseSettings` inheritance; use
  `specx.infrastructure.foundation.settings.BaseRuntimeSettings`.
