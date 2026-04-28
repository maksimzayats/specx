from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest
from management.setup_wizard.git import GitPlan, apply_git_plan, build_git_plan
from management.setup_wizard.models import DatabaseMode, RedisMode, SetupAnswers, StorageMode


def test_git_plan_includes_reinitialize_origin_and_initial_commit(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    answers = _answers(repo_url="https://github.com/acme/acme-api")

    plan = build_git_plan(repo_root=tmp_path, answers=answers)

    assert plan.actions[0].kind == "delete"
    assert plan.actions[0].target == ".git"
    assert _commands(plan=plan) == [
        ("git", "init", "--initial-branch=main"),
        ("git", "remote", "add", "origin", "https://github.com/acme/acme-api"),
        ("git", "add", "--all"),
        ("git", "commit", "-m", "initial commit"),
    ]


def test_blank_repository_url_creates_no_remote_action(tmp_path: Path) -> None:
    plan = build_git_plan(repo_root=tmp_path, answers=_answers(repo_url=None))

    assert ("git", "remote", "add", "origin") not in [
        command[:4] for command in _commands(plan=plan)
    ]


def test_initial_commit_commands_are_skipped_when_declined(tmp_path: Path) -> None:
    plan = build_git_plan(
        repo_root=tmp_path,
        answers=_answers(create_initial_commit=False),
    )

    assert ("git", "add", "--all") not in _commands(plan=plan)
    assert ("git", "commit", "-m", "initial commit") not in _commands(plan=plan)


def test_declined_reinitialize_git_plan_warns_without_actions(tmp_path: Path) -> None:
    plan = build_git_plan(
        repo_root=tmp_path,
        answers=_answers(reinitialize_git_repository=False),
    )

    assert [action.kind for action in plan.actions] == ["warning"]
    assert "template" in plan.actions[0].detail
    assert _commands(plan=plan) == []


def test_missing_git_does_not_remove_existing_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    git_config_path = tmp_path / ".git" / "config"
    _write(git_config_path, "template config\n")
    plan = build_git_plan(repo_root=tmp_path, answers=_answers())
    monkeypatch.setattr(shutil, "which", lambda *_: None)

    with pytest.raises(FileNotFoundError):
        apply_git_plan(plan=plan)

    assert git_config_path.read_text(encoding="utf-8") == "template config\n"


def test_env_remains_ignored_and_not_force_added(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if shutil.which("git") is None:
        pytest.skip("git is required for setup wizard Git tests")

    _configure_git_identity(monkeypatch=monkeypatch)
    _write(tmp_path / ".gitignore", ".env\n")
    _write(tmp_path / ".env", "SECRET_KEY=local-secret\n")
    _write(tmp_path / ".env.example", "SECRET_KEY=replace-me\n")
    _write(tmp_path / "app.py", "print('hello')\n")
    answers = _answers(repo_url=None)
    plan = build_git_plan(repo_root=tmp_path, answers=answers)

    result = apply_git_plan(plan=plan)

    assert result.initial_commit_created is True
    tracked_files = _git(repo_root=tmp_path, args=("ls-files",)).stdout.splitlines()
    assert ".env" not in tracked_files
    assert ".env.example" in tracked_files
    assert "app.py" in tracked_files


def _commands(*, plan: GitPlan) -> list[tuple[str, ...]]:
    return [action.command for action in plan.actions if action.command is not None]


def _answers(
    *,
    repo_url: str | None = "https://github.com/acme/acme-api",
    reinitialize_git_repository: bool = True,
    create_initial_commit: bool = True,
) -> SetupAnswers:
    return SetupAnswers(
        project_name="Example API",
        package_name="example_api",
        distribution_name="example-api",
        docs_site_url=None,
        storage_mode=StorageMode.LOCAL,
        database_mode=DatabaseMode.DOCKER_POSTGRES,
        redis_mode=RedisMode.DOCKER_REDIS,
        keep_docs=True,
        delete_wizard=False,
        overwrite_env=True,
        repo_url=repo_url,
        reinitialize_git_repository=reinitialize_git_repository,
        create_initial_commit=create_initial_commit,
    )


def _configure_git_identity(*, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_AUTHOR_NAME", "FastDjango Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "fastdjango-test@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "FastDjango Test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "fastdjango-test@example.com")


def _git(*, repo_root: Path, args: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    git_path = shutil.which("git")
    if git_path is None:
        msg = "git executable was not found."
        raise FileNotFoundError(msg)

    return subprocess.run(  # noqa: S603
        (git_path, *args),
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
