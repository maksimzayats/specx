from diwire import Container

from fastdjango.foundation.transactions import TransactionFactory
from fastdjango.infrastructure.django.transactions import DjangoTransactionFactory


def register_dependencies(container: Container) -> None:
    container.add(DjangoTransactionFactory, provides=TransactionFactory)
