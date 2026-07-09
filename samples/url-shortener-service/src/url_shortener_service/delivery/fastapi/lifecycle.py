from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from diwire import Container, Injected
from fastapi import FastAPI
from specx.delivery.foundation.lifecycle import BaseLifecycle

from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory


@dataclass(kw_only=True, slots=True)
class FastAPILifecycle(BaseLifecycle[FastAPI]):
    """FastAPI lifespan manager for application-owned resources.

    Example:
        app = FastAPI(lifespan=FastAPILifecycle(...))
    """

    _container: Injected[Container]
    _session_factory: Injected[SQLAlchemySessionFactory]

    def __call__(self, app: FastAPI) -> AbstractAsyncContextManager[None]:
        return self._lifespan(app=app)

    @asynccontextmanager
    async def _lifespan(self, *, app: FastAPI) -> AsyncIterator[None]:
        del app

        try:
            yield
        finally:
            try:
                await self._session_factory.close()
            finally:
                await self._container.aclose()
