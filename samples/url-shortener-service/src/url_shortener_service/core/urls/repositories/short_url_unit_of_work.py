from abc import abstractmethod

from specx.core.foundation.unit_of_work import BaseUnitOfWork
from specx.core.foundation.unit_of_work_manager import BaseUnitOfWorkManager

from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository


class ShortUrlUnitOfWork(BaseUnitOfWork):
    """Active transaction boundary for short URL repositories.

    Example:
        short_url = await unit_of_work.short_urls.find_by_code(code="abc123")
    """

    @property
    @abstractmethod
    def short_urls(self) -> ShortUrlRepository:
        raise NotImplementedError


class ShortUrlUnitOfWorkManager(BaseUnitOfWorkManager[ShortUrlUnitOfWork]):
    """Manager that opens active short URL units of work.

    Example:
        async with short_url_unit_of_work_manager as unit_of_work:
            short_url = await unit_of_work.short_urls.find_by_code(code="abc123")
    """
