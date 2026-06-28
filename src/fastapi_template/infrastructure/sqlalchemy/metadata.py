from fastapi_template.core.authentication.infrastructure.sqlalchemy import (
    models as authentication_models,  # noqa: F401
)
from fastapi_template.core.user.infrastructure.sqlalchemy import (
    models as user_models,  # noqa: F401
)
from fastapi_template.infrastructure.sqlalchemy.base import Base

target_metadata = Base.metadata
