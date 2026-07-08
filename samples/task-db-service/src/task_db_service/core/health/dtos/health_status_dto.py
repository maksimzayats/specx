from dataclasses import dataclass

from specx.foundation.dto import BaseDTO


@dataclass(frozen=True, kw_only=True, slots=True)
class HealthStatusDTO(BaseDTO):
    """DTO returned by the health use case.

    Example:
        HealthStatusDTO(status="ok")
    """

    status: str
