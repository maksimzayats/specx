import pytest
from fastapi import status

from tests._support.clients.fastapi import TestAsyncClientFactory


@pytest.mark.anyio
async def test_health_route_maps_use_case_result_to_response(
    transactional_test_async_client_factory: TestAsyncClientFactory,
) -> None:
    async with transactional_test_async_client_factory() as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
