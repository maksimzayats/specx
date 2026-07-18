from __future__ import annotations

import ast

from specx.testing.architecture.context import (
    ArchitectureContext,
    class_base_name_index,
    class_injected_repository_field_names,
    class_injected_unit_of_work_manager_field_names,
)
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ArchitectureRuleBase,
    _forbidden_use_case_persistence_dependency_fields,
    _is_use_case_class,
    _repository_calls_outside_manager_owned_uow,
    _use_case_imports_persistence_infrastructure,
    _violation,
)


class UseCasesDoNotInjectRepositoriesOrInfrastructureRule(ArchitectureRuleBase):
    """Require persistence access to flow through use-case-owned UoW scopes.

    Use cases should inject services and UoW managers, not repositories,
    SQLAlchemy resources, or concrete infrastructure adapters that bypass
    transaction ownership.
    """

    id: SpecxRuleId = SpecxRuleId.USE_CASES_DO_NOT_INJECT_REPOSITORIES_OR_INFRASTRUCTURE

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        base_index = class_base_name_index(context)
        for path in (context.src_root / "core").glob("*/use_cases/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue

            tree = context.tree(path)
            aliases = context.aliases(path)
            for module in sorted(context.imports(path)):
                if _use_case_imports_persistence_infrastructure(module):
                    violations.append(_violation(self.id, path=path, message=f"imports {module}"))

            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                if not _is_use_case_class(class_node, aliases, base_index):
                    continue

                messages: list[str] = []
                forbidden_fields = _forbidden_use_case_persistence_dependency_fields(
                    class_node,
                    aliases,
                    base_index,
                )
                if forbidden_fields:
                    messages.append(f"injects {forbidden_fields}")

                manager_fields = class_injected_unit_of_work_manager_field_names(
                    class_node,
                    aliases,
                )
                repository_fields = class_injected_repository_field_names(
                    class_node,
                    aliases,
                    base_index,
                )
                for child in class_node.body:
                    if (
                        isinstance(child, (ast.AsyncFunctionDef, ast.FunctionDef))
                        and child.name == "execute"
                    ):
                        bad_calls = _repository_calls_outside_manager_owned_uow(
                            child,
                            manager_fields=manager_fields,
                            repository_fields=repository_fields,
                        )
                        if bad_calls:
                            messages.append(
                                f"calls repositories outside manager-owned UoW {sorted(bad_calls)}",
                            )

                if messages:
                    violations.append(
                        _violation(
                            self.id,
                            path=path,
                            message="; ".join(messages),
                            symbol=class_node.name,
                        )
                    )
        return tuple(violations)
