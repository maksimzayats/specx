from abc import ABC, abstractmethod
from typing import Generic, TypeVar

RegistryT = TypeVar("RegistryT")


class BaseController(ABC, Generic[RegistryT]):
    """Base for delivery controllers that register public routes.

    Example:
        class TasksController(BaseController[APIRouter]):
            def register(self, registry: APIRouter) -> None:
                registry.add_api_route("/api/v1/tasks", self.list_tasks)
    """

    @abstractmethod
    def register(self, registry: RegistryT) -> None:
        raise NotImplementedError
