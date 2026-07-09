from __future__ import annotations

import ast
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


@dataclass(frozen=True, kw_only=True, slots=True)
class PythonSourceFile:
    """Parsed Python file and its lightweight static metadata."""

    path: Path
    tree: ast.Module
    imports: frozenset[str]
    aliases: dict[str, str]


@dataclass(frozen=True, kw_only=True, slots=True)
class PythonAstProject:
    """Static Python source index for a project under inspection."""

    files: dict[Path, PythonSourceFile]

    def source_file(self, path: Path) -> PythonSourceFile:
        return self.files[path]


@dataclass(frozen=True, kw_only=True, slots=True)
class PythonAstScanner:
    """Parse project Python files once so rules can share AST metadata."""

    project_root: Path
    excluded_patterns: tuple[str, ...] = ()

    def scan(self, roots: tuple[Path, ...]) -> PythonAstProject:
        files: dict[Path, PythonSourceFile] = {}
        for root in roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.py")):
                if self._is_excluded(path):
                    continue
                text = path.read_text(encoding="utf-8")
                tree = ast.parse(text, filename=str(path))
                files[path] = PythonSourceFile(
                    path=path,
                    tree=tree,
                    imports=_imports(tree),
                    aliases=_import_aliases(tree),
                )
        return PythonAstProject(files=files)

    def _is_excluded(self, path: Path) -> bool:
        relative = path.relative_to(self.project_root).as_posix()
        return any(fnmatch(relative, pattern) for pattern in self.excluded_patterns)


def _imports(tree: ast.Module) -> frozenset[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module_name = "." * node.level + (node.module or "")
            if module_name:
                modules.add(module_name)
            separator = "" if module_name == "" or module_name.endswith(".") else "."
            modules.update(
                f"{module_name}{separator}{alias.name}" for alias in node.names if alias.name != "*"
            )
    return frozenset(modules)


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = alias.name.split(".")[-1]
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
    return aliases
