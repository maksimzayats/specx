from __future__ import annotations

import pytest
from diwire import Container, DependencyRegistrationPolicy, MissingPolicy


@pytest.fixture
def container() -> Container:
    return Container(
        missing_policy=MissingPolicy.REGISTER_RECURSIVE,
        dependency_registration_policy=DependencyRegistrationPolicy.REGISTER_RECURSIVE,
    )
