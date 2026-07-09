"""FastAPI runtime entrypoint.

Example:
    uv run uvicorn url_shortener_service.delivery.fastapi.__main__:app
"""

from url_shortener_service.delivery.fastapi.factory import FastAPIFactory
from url_shortener_service.ioc.container import get_container

container = get_container()
app_factory = container.resolve(FastAPIFactory)
app = app_factory()
