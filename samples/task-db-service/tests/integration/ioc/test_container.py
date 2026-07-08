from diwire import Container

from task_db_service.delivery.fastapi.factory import FastAPIFactory


def test_container_resolves_fastapi_factory(container: Container) -> None:
    factory = container.resolve(FastAPIFactory)

    assert isinstance(factory, FastAPIFactory)
