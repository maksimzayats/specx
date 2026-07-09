import pytest
from fastapi import FastAPI


@pytest.mark.anyio
async def test_factory_exposes_expected_business_routes(
    fastapi_app: FastAPI,
) -> None:
    openapi_paths = set(fastapi_app.openapi()["paths"])

    assert openapi_paths == {
        "/api/v1/r/{code}",
        "/api/v1/short-urls",
        "/api/v1/short-urls/{code}",
    }


@pytest.mark.anyio
async def test_factory_keeps_business_routes_under_api_v1(
    fastapi_app: FastAPI,
) -> None:
    openapi_route_signatures = {
        (method.upper(), path)
        for path, methods in fastapi_app.openapi()["paths"].items()
        for method in methods
    }

    assert openapi_route_signatures == {
        ("GET", "/api/v1/r/{code}"),
        ("GET", "/api/v1/short-urls/{code}"),
        ("POST", "/api/v1/short-urls"),
    }
