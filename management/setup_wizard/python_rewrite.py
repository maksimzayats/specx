from __future__ import annotations

from typing import override

import libcst as cst
from libcst.helpers import get_full_name_for_node


def rewrite_python_imports(
    source: str,
    *,
    old_package_name: str,
    new_package_name: str,
) -> str:
    if old_package_name == new_package_name:
        return source

    try:
        module = cst.parse_module(source)
    except cst.ParserSyntaxError:
        return source

    transformer = PackageImportTransformer(
        old_package_name=old_package_name,
        new_package_name=new_package_name,
    )
    return module.visit(transformer).code


class PackageImportTransformer(cst.CSTTransformer):
    def __init__(self, *, old_package_name: str, new_package_name: str) -> None:
        self._old_package_name = old_package_name
        self._new_package_name = new_package_name

    @override
    def leave_ImportAlias(
        self,
        _original_node: cst.ImportAlias,
        updated_node: cst.ImportAlias,
    ) -> cst.ImportAlias:
        return updated_node.with_changes(name=self._rename_module_expression(updated_node.name))

    @override
    def leave_ImportFrom(
        self,
        _original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom:
        if updated_node.module is None:
            return updated_node

        return updated_node.with_changes(
            module=self._rename_module_expression(updated_node.module),
        )

    def _rename_module_expression(self, node: cst.BaseExpression) -> cst.BaseExpression:
        module_name = get_full_name_for_node(node)
        if module_name is None:
            return node

        renamed_module_name = self._rename_module_name(module_name=module_name)
        if renamed_module_name == module_name:
            return node

        return cst.parse_expression(renamed_module_name)

    def _rename_module_name(self, *, module_name: str) -> str:
        if module_name == self._old_package_name:
            return self._new_package_name

        prefix = f"{self._old_package_name}."
        if module_name.startswith(prefix):
            return f"{self._new_package_name}.{module_name.removeprefix(prefix)}"

        return module_name
