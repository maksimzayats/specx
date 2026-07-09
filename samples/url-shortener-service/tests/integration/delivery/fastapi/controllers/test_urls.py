import pytest
from diwire import Container
from fastapi import status

from tests._support.clients.fastapi import open_test_async_client


@pytest.mark.anyio
async def test_create_short_url_route_persists_normalized_target(
    container: Container,
) -> None:
    async with open_test_async_client(container) as client:
        create_response = await client.post(
            "/api/v1/short-urls",
            json={"target_url": " HTTPS://Example.COM/docs#top "},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        created_body = create_response.json()
        code = created_body["code"]
        get_response = await client.get(f"/api/v1/short-urls/{code}")

    assert created_body["target_url"] == "https://example.com/docs"

    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json() == created_body


@pytest.mark.anyio
async def test_create_short_url_route_rejects_invalid_target(
    container: Container,
) -> None:
    async with open_test_async_client(container) as client:
        response = await client.post(
            "/api/v1/short-urls",
            json={"target_url": "ftp://example.com/file"},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]["target_url"] == "ftp://example.com/file"


@pytest.mark.anyio
async def test_get_short_url_route_returns_not_found(
    container: Container,
) -> None:
    async with open_test_async_client(container) as client:
        response = await client.get("/api/v1/short-urls/missing")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == {
        "code": "missing",
        "message": "Short URL not found",
    }


@pytest.mark.anyio
async def test_resolve_short_url_route_redirects_to_target(
    container: Container,
) -> None:
    async with open_test_async_client(container) as client:
        create_response = await client.post(
            "/api/v1/short-urls",
            json={"target_url": "https://example.com/docs"},
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        code = create_response.json()["code"]
        response = await client.get(f"/api/v1/r/{code}", follow_redirects=False)

    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["location"] == "https://example.com/docs"
