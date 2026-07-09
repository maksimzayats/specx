from dataclasses import dataclass
from typing import ClassVar

from diwire import Injected
from specx.core.foundation.effect_service import BaseEffectService

from url_shortener_service.core.urls.capabilities.random_short_code_capability import (
    RandomShortCodeCapability,
)
from url_shortener_service.core.urls.dtos.short_url_dto import ShortUrlDTO
from url_shortener_service.core.urls.exceptions.short_code_collision_error import (
    ShortCodeCollisionError,
)
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWork,
)
from url_shortener_service.core.urls.services.target_url_normalizer_service import (
    TargetUrlNormalizerService,
)


@dataclass(kw_only=True, slots=True)
class ShortUrlCreationService(BaseEffectService):
    """Service that creates short URLs inside an active URL unit of work.

    Example:
        short_url = await service.create(
            unit_of_work=unit_of_work,
            target_url="https://example.com/docs",
        )
    """

    _short_code_capability: Injected[RandomShortCodeCapability]
    _target_url_normalizer_service: Injected[TargetUrlNormalizerService]
    _max_code_generation_attempts: ClassVar[int] = 5

    async def create(self, *, unit_of_work: ShortUrlUnitOfWork, target_url: str) -> ShortUrlDTO:
        normalized_target_url = self._target_url_normalizer_service.normalize(
            target_url=target_url,
        )

        for _ in range(self._max_code_generation_attempts):
            code = self._short_code_capability.generate()
            existing_short_url = await unit_of_work.short_urls.find_by_code(code=code)
            if existing_short_url is not None:
                continue

            short_url = await unit_of_work.short_urls.add(
                code=code,
                target_url=normalized_target_url,
            )
            return ShortUrlDTO(
                id=short_url.id,
                code=short_url.code,
                target_url=short_url.target_url,
            )

        raise ShortCodeCollisionError(max_attempts=self._max_code_generation_attempts)
