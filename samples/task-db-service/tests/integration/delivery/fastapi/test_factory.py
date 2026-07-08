import pytest
from diwire import Container

from task_db_service.delivery.fastapi.factory import FastAPIFactory


@pytest.mark.anyio
async def test_factory_registers_expected_routes(transactional_container: Container) -> None:
    app_factory = transactional_container.resolve(FastAPIFactory)
    app = app_factory()

    route_signatures = {
        (method.upper(), path)
        for path, methods in app.openapi()["paths"].items()
        for method in methods
        if path.startswith("/api/v1")
    }

    assert route_signatures == {
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/tasks"),
        ("GET", "/api/v1/tasks/{task_id}"),
        ("POST", "/api/v1/tasks"),
        ("POST", "/api/v1/tasks/{task_id}/complete"),
    }
