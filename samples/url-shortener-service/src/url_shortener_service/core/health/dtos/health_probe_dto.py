from dataclasses import dataclass

from specx.core.foundation.dto import BaseDTO
from specx.core.foundation.enums import BaseStrEnum


class HealthProbeStatusEnum(BaseStrEnum):
    """Enum for operational probe result states.

    Example:
        HealthProbeStatusEnum.PASS
    """

    PASS = "pass"
    FAIL = "fail"


class HealthCheckNameEnum(BaseStrEnum):
    """Enum for named operational readiness checks.

    Example:
        HealthCheckNameEnum.DATABASE
    """

    DATABASE = "database"


@dataclass(frozen=True, kw_only=True, slots=True)
class HealthCheckDTO(BaseDTO):
    """DTO for one operational readiness check.

    Example:
        HealthCheckDTO(
            name=HealthCheckNameEnum.DATABASE,
            status=HealthProbeStatusEnum.PASS,
        )
    """

    name: HealthCheckNameEnum
    status: HealthProbeStatusEnum


@dataclass(frozen=True, kw_only=True, slots=True)
class HealthProbeDTO(BaseDTO):
    """DTO for a reusable operational probe result.

    Example:
        HealthProbeDTO(status=HealthProbeStatusEnum.PASS)
    """

    status: HealthProbeStatusEnum
    checks: tuple[HealthCheckDTO, ...] = ()
