from specx.foundation.infrastructure.sqlalchemy.model import BaseSQLAlchemyModel
from sqlalchemy import Boolean, String, false
from sqlalchemy.orm import Mapped, mapped_column


class TaskModel(BaseSQLAlchemyModel):
    """SQLAlchemy model for persisted task rows.

    Example:
        TaskModel(title="Ship skill", is_completed=False)
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )
