from dataclasses import dataclass

import pytest

from task_db_service.core.tasks.exceptions.invalid_task_title_value_error import (
    InvalidTaskTitleValueError,
)
from task_db_service.core.tasks.services.task_title_normalizer_service import (
    TaskTitleNormalizerService,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class NormalizeTitleCase:
    id: str
    raw_title: str
    expected_title: str


@pytest.mark.parametrize(
    "case",
    [
        NormalizeTitleCase(
            id="trims_edges",
            raw_title="  Ship skill  ",
            expected_title="Ship skill",
        ),
        NormalizeTitleCase(
            id="collapses_inner_space",
            raw_title="Ship   skill",
            expected_title="Ship skill",
        ),
    ],
    ids=lambda case: case.id,
)
def test_normalize_accepts_valid_titles(
    case: NormalizeTitleCase,
    task_title_normalizer_service: TaskTitleNormalizerService,
) -> None:
    result = task_title_normalizer_service.normalize(title=case.raw_title)

    assert result == case.expected_title


def test_normalize_rejects_blank_title(
    task_title_normalizer_service: TaskTitleNormalizerService,
) -> None:
    with pytest.raises(InvalidTaskTitleValueError):
        task_title_normalizer_service.normalize(title="   ")
