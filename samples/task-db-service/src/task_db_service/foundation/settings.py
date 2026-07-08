from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseRuntimeSettings(BaseSettings):
    """Base for runtime settings loaded from environment variables.

    Example:
        class DatabaseSettings(BaseRuntimeSettings):
            database_url: str = "sqlite+aiosqlite:///./app.sqlite3"
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
