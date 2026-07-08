"""FastAPI runtime entrypoint.

Example:
    uv run uvicorn task_db_service.delivery.fastapi.__main__:app
"""

from task_db_service.delivery.fastapi.factory import FastAPIFactory
from task_db_service.ioc.container import get_container

container = get_container()
app_factory = container.resolve(FastAPIFactory)
app = app_factory()
