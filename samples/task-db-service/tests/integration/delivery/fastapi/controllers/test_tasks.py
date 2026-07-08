import pytest
from fastapi import status

from tests._support.clients.fastapi import TestAsyncClientFactory


@pytest.mark.anyio
async def test_task_routes_persist_lifecycle_through_real_app(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        created_response = await client.post(
            "/api/v1/tasks",
            json={"title": "  Ship skill  "},
        )
        created_task = created_response.json()
        task_id = created_task["id"]

        listed_response = await client.get("/api/v1/tasks")
        loaded_response = await client.get(f"/api/v1/tasks/{task_id}")
        completed_response = await client.post(f"/api/v1/tasks/{task_id}/complete")
        reloaded_response = await client.get(f"/api/v1/tasks/{task_id}")

    completed_task = {
        "id": task_id,
        "title": "Ship skill",
        "is_completed": True,
    }

    assert created_response.status_code == status.HTTP_201_CREATED
    assert created_task == {
        "id": task_id,
        "title": "Ship skill",
        "is_completed": False,
    }

    assert listed_response.status_code == status.HTTP_200_OK
    assert listed_response.json() == {"tasks": [created_task]}

    assert loaded_response.status_code == status.HTTP_200_OK
    assert loaded_response.json() == created_task

    assert completed_response.status_code == status.HTTP_200_OK
    assert completed_response.json() == completed_task

    assert reloaded_response.status_code == status.HTTP_200_OK
    assert reloaded_response.json() == completed_task


@pytest.mark.anyio
async def test_create_task_route_maps_invalid_title_to_422(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        response = await client.post("/api/v1/tasks", json={"title": "   "})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json() == {
        "detail": {
            "title": "   ",
            "message": "Task title cannot be blank",
        },
    }


@pytest.mark.anyio
async def test_get_task_route_maps_missing_task_to_404(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        response = await client.get("/api/v1/tasks/404")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": {
            "task_id": 404,
            "message": "Task not found",
        },
    }


@pytest.mark.anyio
async def test_complete_task_route_maps_missing_task_to_404(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        response = await client.post("/api/v1/tasks/404/complete")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "detail": {
            "task_id": 404,
            "message": "Task not found",
        },
    }
