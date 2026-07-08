import pytest

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.core.tasks.services.task_title_normalizer_service import (
    TaskTitleNormalizerService,
)


def test_normalize_collapses_whitespace() -> None:
    result = TaskTitleNormalizerService().normalize(title="  Ship   skill  ")

    assert result == "Ship skill"


def test_normalize_rejects_blank_title() -> None:
    with pytest.raises(InvalidTaskTitleValueError):
        TaskTitleNormalizerService().normalize(title="   ")
