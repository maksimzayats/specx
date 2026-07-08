class BasePureService:
    """Base class for deterministic business helpers.

    Pure services do not perform I/O, do not use repositories, do not use
    gateways, and do not depend on unit-of-work objects, settings, clocks,
    UUID generators, random numbers, HTTP clients, SQLAlchemy, Redis, or SDKs.

    Example:
        class TaskTitleNormalizerService(BasePureService):
            def normalize(self, *, title: str) -> str:
                return " ".join(title.split())
    """
