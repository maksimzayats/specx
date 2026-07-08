from abc import ABC, abstractmethod
from typing import Any


class BaseController(ABC):
    """Base for delivery controllers that register public routes.

    Example:
        class TasksController(BaseController):
            def register(self, registry: APIRouter) -> None:
                registry.add_api_route("/api/v1/tasks", self.list_tasks)
    """

    @abstractmethod
    def register(self, registry: Any) -> None:
        raise NotImplementedError
