from __future__ import annotations

from dataclasses import dataclass, field

from url_shortener_service.core.urls.entities.short_url_entity import ShortUrlEntity
from url_shortener_service.core.urls.repositories.short_url_repository import ShortUrlRepository


@dataclass(kw_only=True, slots=True)
class InMemoryShortUrlRepository(ShortUrlRepository):
    """In-memory repository double for URL unit tests.

    Example:
        repository = InMemoryShortUrlRepository()
    """

    _short_urls: dict[str, ShortUrlEntity] = field(default_factory=dict, init=False)
    _next_id: int = field(default=1, init=False)

    async def add(self, *, code: str, target_url: str) -> ShortUrlEntity:
        short_url = ShortUrlEntity(id=self._next_id, code=code, target_url=target_url)
        self._short_urls[code] = short_url
        self._next_id += 1

        return short_url

    async def find_by_code(self, *, code: str) -> ShortUrlEntity | None:
        return self._short_urls.get(code)

    def add_existing(
        self,
        *,
        code: str,
        target_url: str = "https://example.com/existing",
    ) -> ShortUrlEntity:
        short_url = ShortUrlEntity(id=self._next_id, code=code, target_url=target_url)
        self._short_urls[code] = short_url
        self._next_id += 1

        return short_url

    def snapshot(self) -> tuple[dict[str, ShortUrlEntity], int]:
        return dict(self._short_urls), self._next_id

    def restore(self, snapshot: tuple[dict[str, ShortUrlEntity], int]) -> None:
        self._short_urls, self._next_id = snapshot
