from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from specx.delivery.foundation.fastapi.schema import BaseFastAPISchema
from specx.delivery.foundation.lifecycle import BaseLifecycle, LifecycleState


class ExampleSchema(BaseFastAPISchema):
    """Schema fixture used to verify delivery schema validation."""

    id: int


class ExampleLifecycle(BaseLifecycle[object]):
    """Lifecycle fixture used to verify delivery lifecycle contracts."""

    def __call__(self, app: object) -> AbstractAsyncContextManager[LifecycleState]:
        return self._lifespan(app=app)

    @asynccontextmanager
    async def _lifespan(self, *, app: object) -> AsyncGenerator[None]:
        del app

        yield


def test_delivery_schema_base_supports_pydantic_validation() -> None:
    schema = ExampleSchema.model_validate({"id": 1})

    assert schema.id == 1


def test_delivery_lifecycle_base_supports_async_context_manager() -> None:
    lifecycle = ExampleLifecycle()

    async def run_lifespan() -> bool:
        async with lifecycle(object()):
            return True

    assert asyncio.run(run_lifespan()) is True
