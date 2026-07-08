from dataclasses import dataclass, field

from diwire import Injected
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from task_db_service.foundation.factory import BaseFactory
from task_db_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@dataclass(kw_only=True, slots=True)
class SQLAlchemySessionFactory(BaseFactory):
    """Factory that owns the async SQLAlchemy engine and sessionmaker.

    Example:
        session_maker = SQLAlchemySessionFactory(
            _settings=DatabaseSettings(database_url="sqlite+aiosqlite:///./app.sqlite3"),
        )()
    """

    _settings: Injected[DatabaseSettings]
    _engine: AsyncEngine = field(init=False)
    _session_maker: async_sessionmaker[AsyncSession] = field(init=False)

    def __post_init__(self) -> None:
        self._engine = create_async_engine(self._settings.database_url)
        self._session_maker = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def __call__(self) -> async_sessionmaker[AsyncSession]:
        return self._session_maker
