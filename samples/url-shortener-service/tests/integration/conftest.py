from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from diwire import Container

from tests._support import integration as integration_fixtures

PROJECT_ROOT = Path(__file__).resolve().parents[2]

migrated_database_url = integration_fixtures.migrated_database_url
transactional_session_factory = integration_fixtures.transactional_session_factory
transactional_container = integration_fixtures.transactional_container


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return config


@pytest.fixture
def container(transactional_container: Container) -> Container:
    return transactional_container
