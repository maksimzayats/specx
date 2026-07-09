from dataclasses import dataclass

from diwire import Injected
from specx.core.foundation.query import BaseQuery
from specx.core.foundation.use_case import BaseUseCase

from url_shortener_service.core.urls.dtos.resolved_short_url_dto import ResolvedShortUrlDTO
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.services.short_url_lookup_service import (
    ShortUrlLookupService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class ResolveShortUrlQuery(BaseQuery):
    """Query for resolving a short code to its redirect target.

    Example:
        ResolveShortUrlQuery(code="abc123")
    """

    code: str


@dataclass(kw_only=True, slots=True)
class ResolveShortUrlUseCase(BaseUseCase):
    """Use case that resolves a short URL through the URL UoW manager.

    Example:
        resolved = await use_case.execute(query=ResolveShortUrlQuery(code="abc123"))
    """

    _short_url_lookup_service: Injected[ShortUrlLookupService]
    _unit_of_work_manager: Injected[ShortUrlUnitOfWorkManager]

    async def execute(self, *, query: ResolveShortUrlQuery) -> ResolvedShortUrlDTO:
        async with self._unit_of_work_manager as unit_of_work:
            return await self._short_url_lookup_service.resolve(
                unit_of_work=unit_of_work,
                code=query.code,
            )
