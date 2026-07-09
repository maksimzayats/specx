class BasePureService:
    """Base for deterministic business helpers.

    Pure services do not perform I/O, use repositories, call gateways, or
    depend on unit-of-work objects, settings, clocks, UUID generators, random
    numbers, HTTP clients, SQLAlchemy, Redis, or SDKs.

    Example:
        class TaskTitleNormalizerService(BasePureService):
            def normalize(self, *, title: str) -> str:
                return " ".join(title.split())
    """
