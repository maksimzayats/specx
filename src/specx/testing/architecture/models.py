from __future__ import annotations

import keyword
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from specx._internal.exceptions import BaseSpecxError
from specx.testing.architecture.rule import BaseRule
from specx.testing.architecture.rule_id import SpecxRuleId

if TYPE_CHECKING:
    from specx.testing.architecture.context import ArchitectureContext


RuleIdentifier: TypeAlias = SpecxRuleId | StrEnum | str


class SpecxConfigurationError(BaseSpecxError):
    """Raised when a Specx architecture configuration cannot be evaluated."""


def empty_disabled_rules() -> frozenset[RuleIdentifier]:
    return frozenset()


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecxArchitectureViolation:
    """One architecture rule violation found in a project."""

    rule_id: RuleIdentifier
    message: str
    path: Path | None = None
    symbol: str | None = None

    def format(self, *, project_root: Path) -> str:
        location = ""
        if self.path is not None:
            location = str(self.path.relative_to(project_root))
        if self.symbol is not None:
            location = f"{location}:{self.symbol}" if location else self.symbol
        return f"{location}: {self.message}" if location else self.message


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecxArchitectureReport:
    """Grouped architecture rule results for one checked project."""

    project_root: Path
    violations: tuple[SpecxArchitectureViolation, ...]

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    def format(self) -> str:
        if not self.violations:
            return "Specx architecture checks passed."

        grouped: dict[str, list[SpecxArchitectureViolation]] = defaultdict(list)
        for violation in self.violations:
            grouped[str(violation.rule_id)].append(violation)

        lines = ["Specx architecture violations:"]
        for rule_id in sorted(grouped):
            lines.append(f"- {rule_id}")
            for violation in grouped[rule_id]:
                lines.append(f"  - {violation.format(project_root=self.project_root)}")
        return "\n".join(lines)


ArchitectureRule: TypeAlias = BaseRule[
    RuleIdentifier,
    "ArchitectureContext",
    SpecxArchitectureViolation,
]
ArchitectureRuleType: TypeAlias = type[ArchitectureRule]


@dataclass(frozen=True, kw_only=True, slots=True)
class SpecxArchitectureConfig:
    """Configuration for checking one Python service against Specx rules."""

    project_root: Path
    package_name: str
    disabled_rules: frozenset[RuleIdentifier] = field(default_factory=empty_disabled_rules)
    extra_rules: tuple[ArchitectureRuleType, ...] = ()
    path_exclusions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.package_name.isidentifier() or keyword.iskeyword(self.package_name):
            raise SpecxConfigurationError(
                f"package_name must be one non-keyword Python identifier, "
                f"got {self.package_name!r}",
            )

        normalized_root = self.project_root.expanduser()
        object.__setattr__(self, "project_root", normalized_root)
