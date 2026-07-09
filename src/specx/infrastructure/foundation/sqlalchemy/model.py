from typing import ClassVar

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class BaseSQLAlchemyModel(DeclarativeBase):
    """Compatibility SQLAlchemy declarative base with Specx naming conventions.

    Generated services should define a project-local SQLAlchemy base so metadata
    is not shared globally.

    Example:
        class TaskModel(BaseSQLAlchemyModel):
            __tablename__ = "tasks"
    """

    metadata: ClassVar[MetaData] = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )
