from diwire import Container, DependencyRegistrationPolicy, MissingPolicy

from task_db_service.core.tasks.infrastructure.sqlalchemy.task_unit_of_work import (
    SQLAlchemyTaskUnitOfWorkManager,
)
from task_db_service.core.tasks.repositories.task_unit_of_work import TaskUnitOfWorkManager


def get_container() -> Container:
    container = Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
    _register_dependencies(container)
    return container


def _register_dependencies(container: Container) -> None:
    container.add(
        SQLAlchemyTaskUnitOfWorkManager,
        provides=TaskUnitOfWorkManager,
    )
