from diwire import Container

from fastapi_template.core.shared.throttling.base_async_throttler_factory import (
    BaseAsyncThrottlerFactory,
)
from fastapi_template.core.unit_of_work import UnitOfWork
from fastapi_template.infrastructure.sqlalchemy.unit_of_work import SQLAlchemyUnitOfWork
from fastapi_template.infrastructure.throttled.async_throttler_factory import AsyncThrottlerFactory


def register_dependencies(container: Container) -> None:
    """Register core abstractions that need explicit concrete adapters."""
    container.add(SQLAlchemyUnitOfWork, provides=UnitOfWork)
    container.add(AsyncThrottlerFactory, provides=BaseAsyncThrottlerFactory)
