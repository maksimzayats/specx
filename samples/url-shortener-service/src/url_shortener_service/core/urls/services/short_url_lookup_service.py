from dataclasses import dataclass

from specx.core.foundation.read_service import BaseReadService

from url_shortener_service.core.urls.dtos.resolved_short_url_dto import ResolvedShortUrlDTO
from url_shortener_service.core.urls.dtos.short_url_dto import ShortUrlDTO
from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity
from url_shortener_service.core.urls.exceptions.short_url_not_found_error import (
    ShortUrlNotFoundError,
)
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
)


@dataclass(kw_only=True, slots=True)
class ShortUrlLookupService(BaseReadService):
    """Service that reads short URL DTOs from an active URL unit of work.

    Example:
        short_url = await service.get(unit_of_work=unit_of_work, code="abc123")
    """

    async def get(self, *, unit_of_work: ShortUrlUnitOfWork, code: str) -> ShortUrlDTO:
        short_url = await unit_of_work.short_urls.find_by_code(code=code)
        if short_url is None:
            raise ShortUrlNotFoundError(code=code)

        return self._to_short_url_dto(short_url)

    async def resolve(
        self,
        *,
        unit_of_work: ShortUrlUnitOfWork,
        code: str,
    ) -> ResolvedShortUrlDTO:
        short_url = await unit_of_work.short_urls.find_by_code(code=code)
        if short_url is None:
            raise ShortUrlNotFoundError(code=code)

        return ResolvedShortUrlDTO(code=short_url.code, target_url=short_url.target_url)

    def _to_short_url_dto(self, short_url: ShortUrlEntity) -> ShortUrlDTO:
        return ShortUrlDTO(
            id=short_url.id,
            code=short_url.code,
            target_url=short_url.target_url,
        )
