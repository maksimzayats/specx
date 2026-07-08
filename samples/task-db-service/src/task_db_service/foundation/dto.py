from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base for application payloads returned by core use cases.

    Example:
        class TaskDTO(BaseDTO):
            id: int
            title: str
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)
