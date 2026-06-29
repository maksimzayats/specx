from fastapi_template.foundation.delivery.fastapi.schema import BaseFastAPISchema


class RevokeTokenRequestSchema(BaseFastAPISchema):
    """Define RevokeTokenRequestSchema."""

    refresh_token: str
