from pydantic import BaseModel, ConfigDict


class BaseFastAPISchema(BaseModel):
    """Base for FastAPI request and response schemas.

    Example:
        class TaskResponseSchema(BaseFastAPISchema):
            id: int
            title: str
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)
