class BaseConfigurator:
    """Base for bootstrap objects that apply configuration to runtime systems.

    Example:
        class LoggingConfigurator(BaseConfigurator):
            def configure(self) -> None:
                return None
    """
