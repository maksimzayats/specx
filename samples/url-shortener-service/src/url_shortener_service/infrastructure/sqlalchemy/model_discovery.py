from __future__ import annotations

from importlib import import_module
from pkgutil import walk_packages
from types import ModuleType

MODEL_MODULE_MARKER = ".infrastructure.sqlalchemy.models."


def iter_sqlalchemy_model_module_names(*, core_package: ModuleType) -> tuple[str, ...]:
    core_path = getattr(core_package, "__path__", ())
    module_names = [
        module.name
        for module in walk_packages(core_path, prefix=f"{core_package.__name__}.")
        if MODEL_MODULE_MARKER in module.name and not module.ispkg
    ]
    return tuple(sorted(module_names))


def load_sqlalchemy_model_modules(*, core_package: ModuleType) -> None:
    for module_name in iter_sqlalchemy_model_module_names(core_package=core_package):
        import_module(module_name)
