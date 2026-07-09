from __future__ import annotations

import logging

import pytest
from diwire import Container

from tests.unit.core.urls.capabilities.fake_random_short_code_capability import (
    SequencedShortCodeCapability,
)
from tests.unit.core.urls.repositories.fake_short_url_unit_of_work import (
    InMemoryShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.capabilities.random_short_code_capability import (
    RandomShortCodeCapability,
)
from url_shortener_service.core.urls.exceptions.short_code_collision_error import (
    ShortCodeCollisionError,
)
from url_shortener_service.core.urls.repositories.short_url_unit_of_work import (
    ShortUrlUnitOfWorkManager,
)
from url_shortener_service.core.urls.use_cases.create_short_url import (
    CreateShortUrlCommand,
    CreateShortUrlUseCase,
)


@pytest.mark.anyio
async def test_execute_opens_transaction_and_creates_short_url(
    container: Container,
    caplog: pytest.LogCaptureFixture,
) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    short_code_capability = SequencedShortCodeCapability(codes=["abc1234"])

    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)
    container.add_instance(short_code_capability, provides=RandomShortCodeCapability)

    use_case = container.resolve(CreateShortUrlUseCase)
    logger_name = _enable_caplog_for_use_case(caplog, level=logging.INFO)

    result = await use_case.execute(
        command=CreateShortUrlCommand(target_url=" HTTPS://Example.COM/docs "),
    )

    stored = await unit_of_work_manager.repository.find_by_code(code="abc1234")

    assert result.code == "abc1234"
    assert result.target_url == "https://example.com/docs"
    assert stored is not None
    assert stored.id == result.id
    assert stored.code == result.code
    assert stored.target_url == result.target_url
    assert unit_of_work_manager.entered_count == 1
    assert unit_of_work_manager.committed_count == 1

    created_record = next(
        record for record in caplog.records if record.message == "Created short URL."
    )

    assert created_record.name == logger_name
    assert created_record.__dict__["short_url_id"] == result.id
    assert created_record.__dict__["short_url_code"] == result.code


@pytest.mark.anyio
async def test_execute_logs_collision_failure_without_target_url(
    container: Container,
    caplog: pytest.LogCaptureFixture,
) -> None:
    unit_of_work_manager = InMemoryShortUrlUnitOfWorkManager()
    for code in ("abc1234", "def5678", "ghi9012", "jkl3456", "mno7890"):
        unit_of_work_manager.repository.add_existing(code=code)

    short_code_capability = SequencedShortCodeCapability(
        codes=["abc1234", "def5678", "ghi9012", "jkl3456", "mno7890"],
    )

    container.add_instance(unit_of_work_manager, provides=ShortUrlUnitOfWorkManager)
    container.add_instance(short_code_capability, provides=RandomShortCodeCapability)

    use_case = container.resolve(CreateShortUrlUseCase)
    logger_name = _enable_caplog_for_use_case(caplog, level=logging.WARNING)

    with pytest.raises(ShortCodeCollisionError):
        await use_case.execute(
            command=CreateShortUrlCommand(target_url="https://example.com/private-token"),
        )

    warning_records = [
        record
        for record in caplog.records
        if record.message == "Short URL creation exhausted code generation attempts."
    ]

    assert len(warning_records) == 1
    assert warning_records[0].name == logger_name
    assert "private-token" not in warning_records[0].getMessage()
    assert unit_of_work_manager.rolled_back_count == 1


def _enable_caplog_for_use_case(
    caplog: pytest.LogCaptureFixture,
    *,
    level: int,
) -> str:
    logger_name = _logger_name(CreateShortUrlUseCase)
    logging.getLogger(logger_name).disabled = False
    caplog.set_level(level, logger=logger_name)

    return logger_name


def _logger_name(target: type[object]) -> str:
    return f"{target.__module__}.{target.__qualname__}"
