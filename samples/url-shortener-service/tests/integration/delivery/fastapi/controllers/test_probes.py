from dataclasses import dataclass

import pytest
from diwire import Container
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests._support.clients.fastapi import open_test_async_client
from url_shortener_service.infrastructure.sqlalchemy.session import SQLAlchemySessionFactory
from url_shortener_service.infrastructure.sqlalchemy.settings import DatabaseSettings


@dataclass(kw_only=True, slots=True)
class UnavailableSQLAlchemySessionFactory(SQLAlchemySessionFactory):
    """Session factory double that simulates an unavailable database.

    Example:
        container.add_instance(factory, provides=SQLAlchemySessionFactory)
    """

    def __post_init__(self) -> None:
        pass

    def __call__(self) -> async_sessionmaker[AsyncSession]:
        raise RuntimeError("database unavailable")

    async def close(self) -> None:
        pass


def use_unavailable_database(container: Container) -> None:
    container.add_instance(
        UnavailableSQLAlchemySessionFactory(
            _settings=DatabaseSettings(database_url="sqlite+aiosqlite:///unavailable.sqlite3"),
        ),
        provides=SQLAlchemySessionFactory,
    )


@pytest.mark.anyio
async def test_healthz_returns_process_probe_response(
    container: Container,
) -> None:
    use_unavailable_database(container)

    async with open_test_async_client(container) as client:
        response = await client.get("/healthz")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"status": "pass"}


@pytest.mark.anyio
async def test_readyz_returns_ready_when_database_check_passes(
    container: Container,
) -> None:
    async with open_test_async_client(container) as client:
        response = await client.get("/readyz")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "status": "pass",
        "checks": {"database": {"status": "pass"}},
    }


@pytest.mark.anyio
async def test_readyz_returns_unavailable_when_database_check_fails(
    container: Container,
) -> None:
    use_unavailable_database(container)

    async with open_test_async_client(container) as client:
        response = await client.get("/readyz")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "status": "fail",
        "checks": {"database": {"status": "fail"}},
    }


@pytest.mark.anyio
async def test_api_v1_health_is_not_registered(
    container: Container,
) -> None:
    use_unavailable_database(container)

    async with open_test_async_client(container) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == status.HTTP_404_NOT_FOUND
