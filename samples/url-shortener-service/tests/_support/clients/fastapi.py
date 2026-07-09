from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from diwire import Container
from httpx2 import ASGITransport, AsyncClient

from url_shortener_service.delivery.fastapi.factory import FastAPIFactory


@asynccontextmanager
async def open_test_async_client(container: Container) -> AsyncIterator[AsyncClient]:
    app_factory = container.resolve(FastAPIFactory)
    app = app_factory()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
