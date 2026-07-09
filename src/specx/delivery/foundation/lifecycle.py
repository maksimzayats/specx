from abc import ABC, abstractmethod
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, TypeAlias, TypeVar

AppT = TypeVar("AppT")
LifecycleState: TypeAlias = Mapping[str, Any] | None


class BaseLifecycle(ABC, Generic[AppT]):
    """Base for delivery application lifecycle managers.

    Example:
        class FastAPILifecycle(BaseLifecycle[FastAPI]):
            def __call__(self, app: FastAPI) -> AbstractAsyncContextManager[LifecycleState]:
                return self.lifespan(app)
    """

    @abstractmethod
    def __call__(self, app: AppT) -> AbstractAsyncContextManager[LifecycleState]:
        raise NotImplementedError
