from dataclasses import dataclass, field
from typing import Any, cast

from diwire import Injected
from throttled.asyncio import (
    Quota as AsyncQuota,
    RateLimiterType as AsyncRateLimiterType,
    RedisStore as AsyncRedisStore,
    Throttled as AsyncThrottled,
)

from fastapi_template.core.shared.throttling.base_async_throttler_factory import (
    BaseAsyncThrottlerFactory,
)
from fastapi_template.infrastructure.throttled.async_store_factory import (
    AsyncThrottlerStoreFactory,
)


@dataclass(kw_only=True)
class AsyncThrottlerFactory(BaseAsyncThrottlerFactory):
    """Create async throttled rate-limiters backed by Redis."""

    _store_factory: Injected[AsyncThrottlerStoreFactory]

    _store: AsyncRedisStore = field(init=False)

    def __post_init__(self) -> None:
        """Create the shared async Redis store once per factory instance."""
        self._store = self._store_factory()

    def __call__(
        self,
        quota: AsyncQuota,
        using: AsyncRateLimiterType = AsyncRateLimiterType.TOKEN_BUCKET,
    ) -> AsyncThrottled:
        """Provide an async Redis-backed rate limiter for a quota.

        Returns:
            A configured async throttler.
        """
        return AsyncThrottled(
            using=using.value,
            quota=quota,
            store=cast(Any, self._store),
        )
