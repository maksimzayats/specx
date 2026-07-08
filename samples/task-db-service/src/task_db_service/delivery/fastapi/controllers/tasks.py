from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, HTTPException, status

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.core.tasks.exceptions.task_not_found_error import TaskNotFoundError
from task_db_service.core.tasks.use_cases.complete_task import (
    CompleteTaskCommand,
    CompleteTaskUseCase,
)
from task_db_service.core.tasks.use_cases.create_task import CreateTaskCommand, CreateTaskUseCase
from task_db_service.core.tasks.use_cases.get_task import GetTaskQuery, GetTaskUseCase
from task_db_service.core.tasks.use_cases.list_tasks import ListTasksQuery, ListTasksUseCase
from task_db_service.delivery.fastapi.schemas.task_schema import (
    CreateTaskRequestSchema,
    TaskListResponseSchema,
    TaskResponseSchema,
)
from task_db_service.foundation.delivery.controller import BaseController


@dataclass(kw_only=True, slots=True)
class TasksController(BaseController):
    """FastAPI controller that registers task routes.

    Example:
        TasksController(
            _create_task_use_case=create_task,
            _get_task_use_case=get_task,
            _list_tasks_use_case=list_tasks,
            _complete_task_use_case=complete_task,
        ).register(router)
    """

    _create_task_use_case: Injected[CreateTaskUseCase]
    _get_task_use_case: Injected[GetTaskUseCase]
    _list_tasks_use_case: Injected[ListTasksUseCase]
    _complete_task_use_case: Injected[CompleteTaskUseCase]

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/api/v1/tasks",
            endpoint=self.create_task,
            methods=["POST"],
            response_model=TaskResponseSchema,
            status_code=status.HTTP_201_CREATED,
        )
        registry.add_api_route(
            path="/api/v1/tasks",
            endpoint=self.list_tasks,
            methods=["GET"],
            response_model=TaskListResponseSchema,
        )
        registry.add_api_route(
            path="/api/v1/tasks/{task_id}",
            endpoint=self.get_task,
            methods=["GET"],
            response_model=TaskResponseSchema,
        )
        registry.add_api_route(
            path="/api/v1/tasks/{task_id}/complete",
            endpoint=self.complete_task,
            methods=["POST"],
            response_model=TaskResponseSchema,
        )

    async def create_task(self, request: CreateTaskRequestSchema) -> TaskResponseSchema:
        try:
            result = await self._create_task_use_case.execute(
                command=CreateTaskCommand(title=request.title),
            )
        except InvalidTaskTitleValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"title": error.title, "message": "Task title cannot be blank"},
            ) from error
        return TaskResponseSchema.model_validate(result)

    async def list_tasks(self) -> TaskListResponseSchema:
        result = await self._list_tasks_use_case.execute(query=ListTasksQuery())
        return TaskListResponseSchema.model_validate(result)

    async def get_task(self, task_id: int) -> TaskResponseSchema:
        try:
            result = await self._get_task_use_case.execute(query=GetTaskQuery(task_id=task_id))
        except TaskNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"task_id": error.task_id, "message": "Task not found"},
            ) from error
        return TaskResponseSchema.model_validate(result)

    async def complete_task(self, task_id: int) -> TaskResponseSchema:
        try:
            result = await self._complete_task_use_case.execute(
                command=CompleteTaskCommand(task_id=task_id),
            )
        except TaskNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"task_id": error.task_id, "message": "Task not found"},
            ) from error
        return TaskResponseSchema.model_validate(result)
