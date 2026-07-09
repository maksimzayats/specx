from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter, Response, status
from specx.delivery.foundation.controller import BaseController

from url_shortener_service.core.health.dtos.health_probe_dto import (
    HealthProbeDTO,
    HealthProbeStatusEnum,
)
from url_shortener_service.core.health.use_cases.check_liveness import (
    CheckLivenessQuery,
    CheckLivenessUseCase,
)
from url_shortener_service.core.health.use_cases.check_readiness import (
    CheckReadinessQuery,
    CheckReadinessUseCase,
)
from url_shortener_service.delivery.fastapi.schemas.probe_schema import (
    ProbeCheckResponseSchema,
    ProbeResponseSchema,
)

CACHE_CONTROL_HEADER = "Cache-Control"
NO_STORE_CACHE_CONTROL = "no-store"


@dataclass(kw_only=True, slots=True)
class ProbesController(BaseController[APIRouter]):
    """FastAPI controller that registers operational probe routes.

    Example:
        ProbesController(
            _check_liveness_use_case=liveness,
            _check_readiness_use_case=readiness,
        ).register(router)
    """

    _check_liveness_use_case: Injected[CheckLivenessUseCase]
    _check_readiness_use_case: Injected[CheckReadinessUseCase]

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/healthz",
            endpoint=self.healthz,
            methods=["GET"],
            response_model=ProbeResponseSchema,
            response_model_exclude_none=True,
            include_in_schema=False,
        )
        registry.add_api_route(
            path="/readyz",
            endpoint=self.readyz,
            methods=["GET"],
            response_model=ProbeResponseSchema,
            response_model_exclude_none=True,
            include_in_schema=False,
        )

    def healthz(self, response: Response) -> ProbeResponseSchema:
        response.headers[CACHE_CONTROL_HEADER] = NO_STORE_CACHE_CONTROL

        probe = self._check_liveness_use_case.execute(query=CheckLivenessQuery())

        return self._to_response_schema(probe)

    async def readyz(self, response: Response) -> ProbeResponseSchema:
        response.headers[CACHE_CONTROL_HEADER] = NO_STORE_CACHE_CONTROL

        probe = await self._check_readiness_use_case.execute(
            query=CheckReadinessQuery(),
        )
        if probe.status == HealthProbeStatusEnum.PASS:
            return self._to_response_schema(probe)

        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return self._to_response_schema(probe)

    def _to_response_schema(self, probe: HealthProbeDTO) -> ProbeResponseSchema:
        checks = {
            check.name.value: ProbeCheckResponseSchema(status=check.status)
            for check in probe.checks
        }

        return ProbeResponseSchema(status=probe.status, checks=checks or None)
