import asyncio

from fastdjango.core.health.delivery.celery.schemas import PingResultSchema
from tests.integration.factories import TestCeleryWorkerFactory, TestTasksRegistryFactory


class TestPingTaskController:
    """Tests for PingTaskController."""

    def test_ping_task(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
    ) -> None:
        registry = tasks_registry_factory()
        with celery_worker_factory():
            result = asyncio.run(registry.ping.adelay())
            ping_result = result.get(timeout=10)

        assert ping_result == PingResultSchema(result="pong")
