from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import ClassVar

from httpx2 import ASGITransport, AsyncClient

from task_db_service.delivery.fastapi.factory import FastAPIFactory
from tests._support.bases.factories import ContainerBasedFactory


@dataclass(kw_only=True, slots=True)
class TestAsyncClientFactory(ContainerBasedFactory):
    """Factory for exercising the FastAPI app through ASGI."""

    __test__: ClassVar[bool] = False

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[AsyncClient]:
        app_factory = self._container.resolve(FastAPIFactory)
        app = app_factory()
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
