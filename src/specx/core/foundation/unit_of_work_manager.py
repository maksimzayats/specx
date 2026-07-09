from abc import ABC, abstractmethod
from types import TracebackType
from typing import Generic, Literal, TypeVar

from specx.core.foundation.unit_of_work import BaseUnitOfWork

UnitOfWorkT = TypeVar("UnitOfWorkT", bound=BaseUnitOfWork)


class BaseUnitOfWorkManager(ABC, Generic[UnitOfWorkT]):
    """Base for managers that open, finish, and close active units of work.

    Example:
        async with task_unit_of_work_manager as unit_of_work:
            task = await unit_of_work.tasks.get(task_id=1)
    """

    @abstractmethod
    async def __aenter__(self) -> UnitOfWorkT:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        raise NotImplementedError
