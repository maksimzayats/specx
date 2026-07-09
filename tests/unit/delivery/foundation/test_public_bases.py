from __future__ import annotations

from specx.delivery.foundation.fastapi.schema import BaseFastAPISchema


class ExampleSchema(BaseFastAPISchema):
    """Schema fixture used to verify delivery schema validation."""

    id: int


def test_delivery_schema_base_supports_pydantic_validation() -> None:
    schema = ExampleSchema.model_validate({"id": 1})

    assert schema.id == 1
