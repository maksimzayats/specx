from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    annotation_name,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    is_container_registration_call,
    is_injected_logger_annotation,
    is_logging_logger_expression,
    violation,
)


class LoggingDoesNotInjectLoggersRule(ArchitectureRuleBase):
    """Keep logger naming local to the class that emits log records.

    Runtime logging is configured once through infrastructure. Classes that log
    should create their own named stdlib logger instead of injecting or
    registering `logging.Logger` through DI.
    """

    id: SpecxRuleId = SpecxRuleId.LOGGING_DOES_NOT_INJECT_LOGGERS

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in sorted(context.ast_project.files):
            if path.name == "__init__.py":
                continue

            tree = context.tree(path)
            aliases = context.aliases(path)
            imports = context.imports(path)
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                for child in class_node.body:
                    if not isinstance(child, ast.AnnAssign) or not isinstance(
                        child.target,
                        ast.Name,
                    ):
                        continue
                    if is_injected_logger_annotation(child.annotation, aliases, imports):
                        annotation = annotation_name(child.annotation, aliases)
                        violations.append(
                            violation(
                                self.id,
                                path=path,
                                message=(f"injects logger field {child.target.id}:{annotation}"),
                                symbol=class_node.name,
                            )
                        )

            for node in [child for child in ast.walk(tree) if isinstance(child, ast.Call)]:
                if not is_container_registration_call(node):
                    continue
                provides = next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "provides"),
                    None,
                )
                if provides is not None and is_logging_logger_expression(
                    provides,
                    aliases,
                    imports,
                ):
                    violations.append(
                        violation(
                            self.id,
                            path=path,
                            message="registers logging.Logger in the DI container",
                        )
                    )
        return tuple(violations)
