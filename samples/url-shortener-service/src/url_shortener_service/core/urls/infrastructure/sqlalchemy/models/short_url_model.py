from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from url_shortener_service.foundation.sqlalchemy_model import BaseSQLAlchemyModel


class ShortUrlModel(BaseSQLAlchemyModel):
    """SQLAlchemy model for persisted short URL rows.

    Example:
        ShortUrlModel(code="abc123", target_url="https://example.com/docs")
    """

    __tablename__ = "short_urls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
