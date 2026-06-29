from abc import ABC, abstractmethod


class HealthRepository(ABC):
    """Persistence port for infrastructure readiness checks."""

    @abstractmethod
    async def check_database(self) -> None:
        """Verify that the database can execute a simple query."""
        raise NotImplementedError
