from abc import ABC, abstractmethod

from throttled.asyncio import Quota, RateLimiterType, Throttled

from fastapi_template.foundation.factory import BaseFactory


class BaseAsyncThrottlerFactory(BaseFactory, ABC):
    """Define BaseAsyncThrottlerFactory."""

    @abstractmethod
    def __call__(
        self,
        quota: Quota,
        using: RateLimiterType = RateLimiterType.TOKEN_BUCKET,
    ) -> Throttled:
        """Build an async throttler.

        Returns:
            A configured async throttler.
        """
        raise NotImplementedError
