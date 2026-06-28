from diwire import Container

from fastapi_template.core.unit_of_work import UnitOfWork
from fastapi_template.infrastructure.sqlalchemy.unit_of_work import SQLAlchemyUnitOfWork


def register_dependencies(container: Container) -> None:
    """Run register dependencies."""
    container.add(SQLAlchemyUnitOfWork, provides=UnitOfWork)
