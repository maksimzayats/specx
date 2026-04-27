from diwire import Container

from fastdjango.entrypoints.celery.factories import TasksRegistryFactory
from fastdjango.entrypoints.celery.registry import TasksRegistry
from fastdjango.foundation.transactions import TransactionFactory
from fastdjango.infrastructure.django.transactions import DjangoTransactionFactory


def register_dependencies(container: Container) -> None:
    container.add(DjangoTransactionFactory, provides=TransactionFactory)
    container.add_factory(_build_tasks_registry, provides=TasksRegistry)


def _build_tasks_registry(tasks_registry_factory: TasksRegistryFactory) -> TasksRegistry:
    return tasks_registry_factory()
