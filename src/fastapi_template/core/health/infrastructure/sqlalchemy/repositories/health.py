from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_template.core.health.repositories.health import HealthRepository


class SQLAlchemyHealthRepository(HealthRepository):
    """Database readiness probe backed by the active SQLAlchemy session."""

    def __init__(self, *, session: AsyncSession) -> None:
        """Bind the probe to an existing unit-of-work session."""
        self._session = session

    async def check_database(self) -> None:
        """Execute a minimal query that fails when the database is unavailable."""
        await self._session.execute(text("SELECT 1"))
