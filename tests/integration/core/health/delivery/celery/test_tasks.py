import asyncio

from fastdjango.core.health.delivery.celery.schemas import PingResultSchema
from fastdjango.entrypoints.celery.registry import TasksRegistry
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
            ping_result = asyncio.run(self._ping(registry))

        assert ping_result == PingResultSchema(result="pong")

    async def _ping(self, registry: TasksRegistry) -> PingResultSchema:
        result = await registry.ping.adelay()
        return await result.aget(timeout=10)
