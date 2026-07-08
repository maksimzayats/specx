class BaseService:
    """Base for focused reusable behavior inside the application core.

    Example:
        class TaskTitleNormalizerService(BaseService):
            def normalize(self, *, title: str) -> str:
                return title.strip()
    """
