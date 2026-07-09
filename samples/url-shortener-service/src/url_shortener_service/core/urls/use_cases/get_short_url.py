from dataclasses import dataclass

from diwire import Injected
from specx.core.foundation.query import BaseQuery
from specx.core.foundation.use_case import BaseUseCase

from url_shortener_service.core.urls.dtos.short_url_dto import ShortUrlDTO
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.services.short_url_lookup_service import (
    ShortUrlLookupService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class GetShortUrlQuery(BaseQuery):
    """Query for reading one short URL by code.

    Example:
        GetShortUrlQuery(code="abc123")
    """

    code: str


@dataclass(kw_only=True, slots=True)
class GetShortUrlUseCase(BaseUseCase):
    """Use case that reads one short URL through the URL UoW manager.

    Example:
        short_url = await use_case.execute(query=GetShortUrlQuery(code="abc123"))
    """

    _short_url_lookup_service: Injected[ShortUrlLookupService]
    _unit_of_work_manager: Injected[ShortUrlUnitOfWorkManager]

    async def execute(self, *, query: GetShortUrlQuery) -> ShortUrlDTO:
        async with self._unit_of_work_manager as unit_of_work:
            return await self._short_url_lookup_service.get(
                unit_of_work=unit_of_work,
                code=query.code,
            )
