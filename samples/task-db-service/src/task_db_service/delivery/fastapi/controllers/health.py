from dataclasses import dataclass

from diwire import Injected
from fastapi import APIRouter

from task_db_service.core.health.use_cases.check_health import (
    CheckHealthQuery,
    CheckHealthUseCase,
)
from task_db_service.delivery.fastapi.schemas.health_schema import HealthResponseSchema
from task_db_service.foundation.delivery.controller import BaseController


@dataclass(kw_only=True, slots=True)
class HealthController(BaseController):
    """FastAPI controller that registers health routes.

    Example:
        HealthController(_check_health_use_case=use_case).register(router)
    """

    _check_health_use_case: Injected[CheckHealthUseCase]

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/api/v1/health",
            endpoint=self.check_health,
            methods=["GET"],
            response_model=HealthResponseSchema,
        )

    def check_health(self) -> HealthResponseSchema:
        result = self._check_health_use_case.execute(query=CheckHealthQuery())
        return HealthResponseSchema.model_validate(result)
