from typing import ClassVar, Self

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseRuntimeSettings(BaseSettings):
    """Base for runtime settings loaded from environment variables.

    Example:
        from pydantic import SecretStr

        class DatabaseSettings(BaseRuntimeSettings):
            url: SecretStr
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @classmethod
    def from_environment(cls) -> Self:
        """Load the settings from their configured runtime sources.

        Pydantic's type signature cannot express that required fields may be
        supplied by environment, dotenv, secrets, or custom settings sources.
        Keep that unavoidable typing boundary in this shared constructor.

        Example:
            settings = DatabaseSettings.from_environment()
        """

        return cls()
