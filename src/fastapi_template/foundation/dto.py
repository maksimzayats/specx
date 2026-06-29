from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base Pydantic model for core command and result payloads."""

    model_config = ConfigDict(from_attributes=True)
