from dataclasses import dataclass

from diwire import Injected
from specx.core.foundation.command import BaseCommand
from specx.core.foundation.use_case import BaseUseCase

from url_shortener_service.core.urls.dtos.short_url_dto import ShortUrlDTO
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.services.short_url_creation_service import (
    ShortUrlCreationService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateShortUrlCommand(BaseCommand):
    """Command for creating a short URL.

    Example:
        CreateShortUrlCommand(target_url="https://example.com/docs")
    """

    target_url: str


@dataclass(kw_only=True, slots=True)
class CreateShortUrlUseCase(BaseUseCase):
    """Use case that creates a short URL through the URL UoW manager.

    Example:
        short_url = await use_case.execute(command=CreateShortUrlCommand(target_url=url))
    """

    _short_url_creation_service: Injected[ShortUrlCreationService]
    _unit_of_work_manager: Injected[ShortUrlUnitOfWorkManager]

    async def execute(self, *, command: CreateShortUrlCommand) -> ShortUrlDTO:
        async with self._unit_of_work_manager as unit_of_work:
            return await self._short_url_creation_service.create(
                unit_of_work=unit_of_work,
                target_url=command.target_url,
            )
