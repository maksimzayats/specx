from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, FastAPI
from specx.core.foundation.factory import BaseFactory

from url_shortener_service.delivery.fastapi.controllers.probes import ProbesController
from url_shortener_service.delivery.fastapi.controllers.urls import UrlsController


@dataclass(kw_only=True, slots=True)
class FastAPIFactory(BaseFactory):
    """Factory that composes the FastAPI application.

    Example:
        app = FastAPIFactory(
            _probes_controller=probes_controller,
            _urls_controller=urls_controller,
        )()
    """

    _probes_controller: Injected[ProbesController]
    _urls_controller: Injected[UrlsController]

    def __call__(self) -> FastAPI:
        app = FastAPI(title="URL Shortener Service", redoc_url=None)

        probes_router = APIRouter(tags=["probes"])
        self._probes_controller.register(probes_router)
        app.include_router(probes_router)

        urls_router = APIRouter(tags=["urls"])
        self._urls_controller.register(urls_router)
        app.include_router(urls_router)

        return app
