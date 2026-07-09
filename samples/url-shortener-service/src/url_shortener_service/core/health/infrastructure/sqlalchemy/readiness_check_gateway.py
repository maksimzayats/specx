import asyncio
from dataclasses import dataclass
from typing import Final

from diwire import Injected
from sqlalchemy import text

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthCheckDTO,
    HealthCheckNameEnum,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.gateways.readiness_check_gateway import (
    ReadinessCheckGateway,
)
from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory

DATABASE_CHECK_NAME: Final = HealthCheckNameEnum.DATABASE
DATABASE_CHECK_TIMEOUT_SECONDS: Final = 1.0


@dataclass(kw_only=True, slots=True)
class SQLAlchemyReadinessCheckGateway(ReadinessCheckGateway):
    """SQLAlchemy readiness adapter for operational database checks.

    External effect: opens a SQLAlchemy session and executes a bounded probe query.

    Example:
        checks = await gateway.check()
    """

    _session_factory: Injected[SQLAlchemySessionFactory]

    async def check(self) -> tuple[HealthCheckDTO, ...]:
        try:
            session_maker = self._session_factory()
            async with session_maker() as session:
                await asyncio.wait_for(
                    session.execute(text("SELECT 1")),
                    timeout=DATABASE_CHECK_TIMEOUT_SECONDS,
                )
        except Exception:
            return (
                HealthCheckDTO(
                    name=DATABASE_CHECK_NAME,
                    status=HealthProbeStatusEnum.FAIL,
                ),
            )

        return (
            HealthCheckDTO(
                name=DATABASE_CHECK_NAME,
                status=HealthProbeStatusEnum.PASS,
            ),
        )
