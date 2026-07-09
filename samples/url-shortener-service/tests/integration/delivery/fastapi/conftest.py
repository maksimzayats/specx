from __future__ import annotations

import pytest
from diwire import Container
from fastapi import FastAPI

from url_shortener_service.delivery.fastapi.factory import FastAPIFactory


@pytest.fixture
def fastapi_app(container: Container) -> FastAPI:
    app_factory = container.resolve(FastAPIFactory)

    return app_factory()
