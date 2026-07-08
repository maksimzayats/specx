from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from diwire import Container
from fastapi.testclient import TestClient

from task_db_service.delivery.fastapi.factory import FastAPIFactory
from task_db_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@pytest.fixture
def migrated_container(
    alembic_config: Config,
    container: Container,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Container:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api.sqlite3'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(alembic_config, "head")
    container.add_instance(
        DatabaseSettings(database_url=database_url),
        provides=DatabaseSettings,
    )
    return container


def test_task_routes_create_list_get_and_complete_task(migrated_container: Container) -> None:
    app = migrated_container.resolve(FastAPIFactory)()

    with TestClient(app) as client:
        created_response = client.post("/api/v1/tasks", json={"title": "  Ship skill  "})
        listed_response = client.get("/api/v1/tasks")
        loaded_response = client.get("/api/v1/tasks/1")
        completed_response = client.post("/api/v1/tasks/1/complete")
        missing_response = client.get("/api/v1/tasks/404")

    assert created_response.status_code == 201
    assert created_response.json() == {
        "id": 1,
        "title": "Ship skill",
        "is_completed": False,
    }
    assert listed_response.status_code == 200
    assert listed_response.json() == {
        "tasks": [{"id": 1, "title": "Ship skill", "is_completed": False}],
    }
    assert loaded_response.status_code == 200
    assert loaded_response.json() == {"id": 1, "title": "Ship skill", "is_completed": False}
    assert completed_response.status_code == 200
    assert completed_response.json() == {"id": 1, "title": "Ship skill", "is_completed": True}
    assert missing_response.status_code == 404


def test_task_route_rejects_blank_title(migrated_container: Container) -> None:
    app = migrated_container.resolve(FastAPIFactory)()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/tasks", json={"title": "   "})

    assert response.status_code == 422
    assert response.json() == {
        "detail": {
            "title": "   ",
            "message": "Task title cannot be blank",
        },
    }


def test_health_route_returns_ok(container: Container) -> None:
    app = container.resolve(FastAPIFactory)()

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
