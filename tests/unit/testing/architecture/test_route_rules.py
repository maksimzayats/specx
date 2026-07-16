from __future__ import annotations

from pathlib import Path

from specx.testing.architecture import (
    SpecxArchitectureConfig,
    SpecxRuleId,
    check_specx_architecture,
)


def test_public_routes_rule_accepts_api_routes_and_operational_probes(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "controllers" / "probes.py",
        "class ProbesController:\n"
        "    def register(self, registry):\n"
        "        registry.add_api_route(path='/healthz', endpoint=self.healthz, methods=['GET'])\n"
        "        registry.add_api_route(path='/readyz', endpoint=self.readyz, methods=['GET'])\n"
        "        registry.add_api_route(\n"
        "            path='/api/v1/orders', endpoint=self.orders, methods=['GET']\n"
        "        )\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            extend_select=frozenset({"fastapi"}),
            disabled_rules=_disable_all_except(SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS),
        )
    )

    assert report.violations == ()


def test_public_routes_rule_rejects_other_unversioned_routes(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "src" / "demo_service" / "delivery" / "fastapi" / "controllers" / "status.py",
        "class StatusController:\n"
        "    def register(self, registry):\n"
        "        registry.add_api_route(path='/health', endpoint=self.health, methods=['GET'])\n"
        "        registry.add_api_route(path='/metrics', endpoint=self.metrics, methods=['GET'])\n",
    )

    report = check_specx_architecture(
        SpecxArchitectureConfig(
            project_root=tmp_path,
            package_name="demo_service",
            extend_select=frozenset({"fastapi"}),
            disabled_rules=_disable_all_except(SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS),
        )
    )

    assert [(violation.rule_id, violation.message) for violation in report.violations] == [
        (SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS, "uses '/health'"),
        (SpecxRuleId.PUBLIC_ROUTES_USE_FULL_API_V1_PATHS, "uses '/metrics'"),
    ]
    assert [(violation.line, violation.column) for violation in report.violations] == [
        (3, 37),
        (4, 37),
    ]


def _disable_all_except(rule_id: SpecxRuleId) -> frozenset[SpecxRuleId]:
    return frozenset(candidate for candidate in SpecxRuleId if candidate != rule_id)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
