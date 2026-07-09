class BaseDeliveryService:
    """Base for delivery-only helper services such as auth or rate limiting.

    Example:
        class ApiKeyParsingService(BaseDeliveryService):
            def parse(self, *, header: str) -> str:
                return header.removeprefix("Bearer ")
    """
