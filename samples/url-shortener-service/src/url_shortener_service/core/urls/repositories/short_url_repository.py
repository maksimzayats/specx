from abc import abstractmethod

from specx.core.foundation.repository import BaseRepository

from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity


class ShortUrlRepository(BaseRepository):
    """Repository port for owned short URL persistence.

    Example:
        short_url = await repository.find_by_code(code="abc123")
    """

    @abstractmethod
    async def add(self, *, code: str, target_url: str) -> ShortUrlEntity:
        raise NotImplementedError

    @abstractmethod
    async def find_by_code(self, *, code: str) -> ShortUrlEntity | None:
        raise NotImplementedError
