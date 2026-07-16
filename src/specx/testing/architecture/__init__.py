from __future__ import annotations

from specx.testing.architecture.checker import assert_specx_architecture, check_specx_architecture
from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import (
    RuleIdentifier,
    SpecxArchitectureConfig,
    SpecxArchitectureReport,
    SpecxArchitectureViolation,
    SpecxArchitectureWarning,
    SpecxConfigurationError,
)
from specx.testing.architecture.registry import SpecxRuleRegistryError
from specx.testing.architecture.rule import BaseRule, SpecxRuleMetadata
from specx.testing.architecture.rule_id import SpecxRuleId

__all__ = [
    "ArchitectureContext",
    "BaseRule",
    "RuleIdentifier",
    "SpecxArchitectureConfig",
    "SpecxArchitectureReport",
    "SpecxArchitectureViolation",
    "SpecxArchitectureWarning",
    "SpecxConfigurationError",
    "SpecxRuleId",
    "SpecxRuleMetadata",
    "SpecxRuleRegistryError",
    "assert_specx_architecture",
    "check_specx_architecture",
]
