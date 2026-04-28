from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from management.setup_wizard.models import SetupAnswers

INITIAL_COMMIT_MESSAGE = "initial commit"
INITIAL_BRANCH_NAME = "main"


@dataclass(frozen=True, kw_only=True)
class GitAction:
    kind: Literal["delete", "command", "warning"]
    target: str
    detail: str
    command: tuple[str, ...] | None = None


@dataclass(frozen=True, kw_only=True)
class GitPlan:
    repo_root: Path
    reinitialize_git_repository: bool
    repo_url: str | None
    create_initial_commit: bool
    actions: tuple[GitAction, ...]


@dataclass(frozen=True, kw_only=True)
class GitSetupResult:
    reinitialized: bool
    origin_added: bool = False
    initial_commit_created: bool = False
    initial_commit_failed: bool = False
    initial_commit_stdout: str = ""
    initial_commit_stderr: str = ""


def build_git_plan(*, repo_root: Path, answers: SetupAnswers) -> GitPlan:
    actions: list[GitAction] = []
    if not answers.reinitialize_git_repository:
        actions.append(
            GitAction(
                kind="warning",
                target=".git/config",
                detail="Existing Git remote may still point at the template",
            ),
        )
        return GitPlan(
            repo_root=repo_root,
            reinitialize_git_repository=False,
            repo_url=answers.repo_url,
            create_initial_commit=False,
            actions=tuple(actions),
        )

    if (repo_root / ".git").exists():
        actions.append(
            GitAction(
                kind="delete",
                target=".git",
                detail="Remove template Git history and remotes",
            ),
        )

    actions.append(
        GitAction(
            kind="command",
            target="git init --initial-branch=main",
            detail="Initialize a fresh Git repository",
            command=("git", "init", f"--initial-branch={INITIAL_BRANCH_NAME}"),
        ),
    )

    if answers.repo_url is not None:
        actions.append(
            GitAction(
                kind="command",
                target=f"git remote add origin {answers.repo_url}",
                detail="Set Git origin to the entered repository URL",
                command=("git", "remote", "add", "origin", answers.repo_url),
            ),
        )

    if answers.create_initial_commit:
        actions.extend(
            (
                GitAction(
                    kind="command",
                    target="git add --all",
                    detail="Stage generated project files",
                    command=("git", "add", "--all"),
                ),
                GitAction(
                    kind="command",
                    target='git commit -m "initial commit"',
                    detail="Create the initial project commit",
                    command=("git", "commit", "-m", INITIAL_COMMIT_MESSAGE),
                ),
            ),
        )

    return GitPlan(
        repo_root=repo_root,
        reinitialize_git_repository=True,
        repo_url=answers.repo_url,
        create_initial_commit=answers.create_initial_commit,
        actions=tuple(actions),
    )


def apply_git_plan(*, plan: GitPlan) -> GitSetupResult:
    if not plan.reinitialize_git_repository:
        return GitSetupResult(reinitialized=False)

    _git_executable()
    git_dir = plan.repo_root / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)

    _run_git_command(command=("git", "init", f"--initial-branch={INITIAL_BRANCH_NAME}"), plan=plan)

    origin_added = False
    if plan.repo_url is not None:
        _run_git_command(command=("git", "remote", "add", "origin", plan.repo_url), plan=plan)
        origin_added = True

    if not plan.create_initial_commit:
        return GitSetupResult(reinitialized=True, origin_added=origin_added)

    _run_git_command(command=("git", "add", "--all"), plan=plan)
    git_path = _git_executable()
    commit_result = subprocess.run(  # noqa: S603
        (git_path, "commit", "-m", INITIAL_COMMIT_MESSAGE),
        cwd=plan.repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    if commit_result.returncode != 0:
        return GitSetupResult(
            reinitialized=True,
            origin_added=origin_added,
            initial_commit_failed=True,
            initial_commit_stdout=commit_result.stdout,
            initial_commit_stderr=commit_result.stderr,
        )

    return GitSetupResult(
        reinitialized=True,
        origin_added=origin_added,
        initial_commit_created=True,
        initial_commit_stdout=commit_result.stdout,
        initial_commit_stderr=commit_result.stderr,
    )


def _run_git_command(*, command: tuple[str, ...], plan: GitPlan) -> None:
    subprocess.run(  # noqa: S603
        (_git_executable(), *command[1:]),
        cwd=plan.repo_root,
        check=True,
    )


def _git_executable() -> str:
    git_path = shutil.which("git")
    if git_path is None:
        msg = "git executable was not found."
        raise FileNotFoundError(msg)

    return git_path
