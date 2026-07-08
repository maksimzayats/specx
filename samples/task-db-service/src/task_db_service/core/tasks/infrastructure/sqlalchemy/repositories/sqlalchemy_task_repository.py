from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from task_db_service.core.tasks.entities.task_entity import TaskEntity
from task_db_service.core.tasks.infrastructure.sqlalchemy.models.task_model import TaskModel
from task_db_service.core.tasks.repositories.task_repository import TaskRepository


@dataclass(kw_only=True, slots=True)
class SQLAlchemyTaskRepository(TaskRepository):
    """SQLAlchemy adapter for task persistence.

    Example:
        task = await repository.get(task_id=1)
    """

    _session: AsyncSession

    async def add(self, *, title: str) -> TaskEntity:
        model = TaskModel(title=title, is_completed=False)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def get(self, *, task_id: int) -> TaskEntity | None:
        model = await self._get_model(task_id=task_id)
        if model is None:
            return None
        return self._to_entity(model)

    async def list(self) -> list[TaskEntity]:
        result = await self._session.execute(select(TaskModel).order_by(TaskModel.id))
        return [self._to_entity(model) for model in result.scalars()]

    async def complete(self, *, task_id: int) -> TaskEntity | None:
        model = await self._get_model(task_id=task_id)
        if model is None:
            return None
        model.is_completed = True
        await self._session.flush()
        return self._to_entity(model)

    async def _get_model(self, *, task_id: int) -> TaskModel | None:
        result = await self._session.execute(select(TaskModel).where(TaskModel.id == task_id))
        return result.scalar_one_or_none()

    def _to_entity(self, model: TaskModel) -> TaskEntity:
        return TaskEntity(
            id=model.id,
            title=model.title,
            is_completed=model.is_completed,
        )
