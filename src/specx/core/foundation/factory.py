class BaseFactory:
    """Base for classes that compose or create runtime objects.

    Example:
        class FastAPIFactory(BaseFactory):
            def __call__(self) -> FastAPI:
                return FastAPI()
    """

    __slots__ = ()
