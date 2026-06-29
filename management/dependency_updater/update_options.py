from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class UpdateOptions:
    """Configure dependency updater behavior."""

    dry_run: bool = False
    upgrade_lock: bool = True
    update_pyproject: bool = True
    update_actions: bool = True
    update_containers: bool = True
