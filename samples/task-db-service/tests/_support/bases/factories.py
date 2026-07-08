from __future__ import annotations

from dataclasses import dataclass

from diwire import Container
from specx.foundation.factory import BaseFactory


@dataclass(kw_only=True, slots=True)
class ContainerBasedFactory(BaseFactory):
    """Base test factory for helpers that resolve from a per-test container."""

    _container: Container
