from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity
from url_shortener_service.core.urls.infrastructure.sqlalchemy.models.short_url_model import (
    ShortUrlModel,
)
from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository


@dataclass(kw_only=True, slots=True)
class SQLAlchemyShortUrlRepository(ShortUrlRepository):
    """SQLAlchemy adapter for short URL persistence.

    Example:
        short_url = await repository.find_by_code(code="abc123")
    """

    _session: AsyncSession

    async def add(self, *, code: str, target_url: str) -> ShortUrlEntity:
        model = ShortUrlModel(code=code, target_url=target_url)
        self._session.add(model)
        await self._session.flush()

        return self._to_entity(model)

    async def find_by_code(self, *, code: str) -> ShortUrlEntity | None:
        result = await self._session.execute(
            select(ShortUrlModel).where(ShortUrlModel.code == code),
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_entity(model)

    def _to_entity(self, model: ShortUrlModel) -> ShortUrlEntity:
        return ShortUrlEntity(
            id=model.id,
            code=model.code,
            target_url=model.target_url,
        )
