from specx.infrastructure.foundation.settings import BaseRuntimeSettings


class DatabaseSettings(BaseRuntimeSettings):
    """Settings for SQLAlchemy database connectivity.

    Example:
        DatabaseSettings(database_url="sqlite+aiosqlite:///./app.sqlite3")
    """

    database_url: str = "sqlite+aiosqlite:///./url_shortener_service.sqlite3"
