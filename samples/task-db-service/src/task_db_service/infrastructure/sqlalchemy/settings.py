from specx.foundation.settings import BaseRuntimeSettings


class DatabaseSettings(BaseRuntimeSettings):
    """Settings for SQLAlchemy database connectivity.

    Example:
        DatabaseSettings(database_url="sqlite+aiosqlite:///./app.sqlite3")
    """

    database_url: str = "sqlite+aiosqlite:///./task_db_service.sqlite3"
