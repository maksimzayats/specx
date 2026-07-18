from __future__ import annotations

import ast

from specx.testing.architecture.context import ArchitectureContext
from specx.testing.architecture.models import SpecxArchitectureViolation
from specx.testing.architecture.rule_id import SpecxRuleId
from specx.testing.architecture.rules._shared import (
    ALLOWED_UNVERSIONED_OPERATIONAL_ROUTE_PATHS,
    ArchitectureRuleBase,
    violation,
)


class PublicRoutesUseFullAPIV1PathsRule(ArchitectureRuleBase):
    """Require public business route registrations to use full `/api/v1/...` paths.

    Full route paths make public API shape visible at each registration site.
    Operational probe routes are allowed as explicit unversioned exceptions.
    """

    id: SpecxRuleId = SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS
    family = "fastapi"
    default_enabled = False
    required_project_surface: str | None = "delivery/fastapi"

    def check(self, context: ArchitectureContext) -> tuple[SpecxArchitectureViolation, ...]:
        violations: list[SpecxArchitectureViolation] = []
        for path in (context.src_root / "delivery").glob("**/controllers/**/*.py"):
            if path.name == "__init__.py" or path not in context.ast_project.files:
                continue
            tree = context.tree(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_api_route":
                    continue
                path_keyword = next(
                    (keyword for keyword in node.keywords if keyword.arg == "path"),
                    None,
                )
                path_expression = (
                    path_keyword.value
                    if path_keyword is not None
                    else node.args[0]
                    if node.args
                    else None
                )
                if not isinstance(path_expression, ast.Constant):
                    violations.append(
                        violation(
                            self.id,
                            path=path,
                            message="has dynamic route path",
                            node=node,
                        )
                    )
                    continue
                route_path = path_expression.value
                if not isinstance(route_path, str):
                    violations.append(
                        violation(
                            self.id,
                            path=path,
                            message=f"uses {route_path!r}",
                            node=path_expression,
                        )
                    )
                    continue
                if route_path in ALLOWED_UNVERSIONED_OPERATIONAL_ROUTE_PATHS:
                    continue
                if not route_path.startswith("/api/v1/"):
                    violations.append(
                        violation(
                            self.id,
                            path=path,
                            message=f"uses {route_path!r}",
                            node=path_expression,
                        )
                    )
        return tuple(violations)
