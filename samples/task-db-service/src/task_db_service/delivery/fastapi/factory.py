from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, FastAPI

from task_db_service.delivery.fastapi.controllers.health import HealthController
from task_db_service.delivery.fastapi.controllers.tasks import TasksController
from task_db_service.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class FastAPIFactory(BaseFactory):
    """Factory that composes the FastAPI application.

    Example:
        app = FastAPIFactory(
            _health_controller=health_controller,
            _tasks_controller=tasks_controller,
        )()
    """

    _health_controller: Injected[HealthController]
    _tasks_controller: Injected[TasksController]

    def __call__(self) -> FastAPI:
        app = FastAPI(title="Task DB Service", redoc_url=None)

        health_router = APIRouter(tags=["health"])
        self._health_controller.register(health_router)
        app.include_router(health_router)

        tasks_router = APIRouter(tags=["tasks"])
        self._tasks_controller.register(tasks_router)
        app.include_router(tasks_router)

        return app
