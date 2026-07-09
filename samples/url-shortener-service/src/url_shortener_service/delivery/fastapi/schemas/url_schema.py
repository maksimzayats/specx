from specx.delivery.foundation.fastapi.schema import BaseFastAPISchema


class CreateShortUrlRequestSchema(BaseFastAPISchema):
    """FastAPI request schema for short URL creation.

    Example:
        CreateShortUrlRequestSchema(target_url="https://example.com/docs")
    """

    target_url: str


class ShortUrlResponseSchema(BaseFastAPISchema):
    """FastAPI response schema for one short URL.

    Example:
        ShortUrlResponseSchema(
            id=1,
            code="abc123",
            target_url="https://example.com/docs",
        )
    """

    id: int
    code: str
    target_url: str
