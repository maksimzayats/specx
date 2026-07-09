from diwire import Container, DependencyRegistrationPolicy, MissingPolicy

from url_shortener_service.core.health.gateways.readiness_check_gateway import (
    ReadinessCheckGateway,
)
from url_shortener_service.core.health.infrastructure.sqlalchemy.readiness_check_gateway import (
    SQLAlchemyReadinessCheckGateway,
)
from url_shortener_service.core.urls.infrastructure.sqlalchemy.short_url_unit_of_work import (
    SQLAlchemyShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)


def get_container() -> Container:
    container = Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
    container.add_instance(container, provides=Container)
    _register_dependencies(container)

    return container


def _register_dependencies(container: Container) -> None:
    container.add(
        SQLAlchemyReadinessCheckGateway,
        provides=ReadinessCheckGateway,
    )
    container.add(
        SQLAlchemyShortUrlUnitOfWorkManager,
        provides=ShortUrlUnitOfWorkManager,
    )
