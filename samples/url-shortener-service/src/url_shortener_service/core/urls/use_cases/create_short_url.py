import logging
from dataclasses import dataclass, field

from diwire import Injected
from specx.core.foundation.command import BaseCommand
from specx.core.foundation.use_case import BaseUseCase

from url_shortener_service.core.urls.dtos.short_url_dto import ShortUrlDTO
from url_shortener_service.core.urls.exceptions.short_code_collision_error import (
    ShortCodeCollisionError,
)
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
    _logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
        )

    async def execute(self, *, command: CreateShortUrlCommand) -> ShortUrlDTO:
        try:
            async with self._unit_of_work_manager as unit_of_work:
                short_url = await self._short_url_creation_service.create(
                    unit_of_work=unit_of_work,
                    target_url=command.target_url,
                )
        except ShortCodeCollisionError:
            self._logger.warning("Short URL creation exhausted code generation attempts.")
            raise

        self._logger.info(
            "Created short URL.",
            extra={
                "short_url_id": short_url.id,
                "short_url_code": short_url.code,
            },
        )

        return short_url
