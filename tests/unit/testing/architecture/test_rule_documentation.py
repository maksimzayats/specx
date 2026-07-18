from __future__ import annotations

import ast
import re
from pathlib import Path

from specx.testing.architecture.rules import BUILT_IN_RULES

REPOSITORY_ROOT = Path(__file__).parents[4]
RULE_DOCS_ROOT = REPOSITORY_ROOT / "docs" / "rules"
RULE_REFERENCE_PATH = REPOSITORY_ROOT / "docs" / "pages" / "RulesReference.mdx"
REQUIRED_HEADINGS = (
    "### Why this exists",
    "### Failing example",
    "### Passing example",
    "### Detection notes",
)


def test_every_builtin_rule_has_one_complete_reference() -> None:
    documented_rules = {
        _string_export(source, "ruleId"): (path, source)
        for path in sorted(RULE_DOCS_ROOT.glob("*.mdx"))
        if (source := path.read_text(encoding="utf-8"))
    }
    built_in_rules = {str(rule.metadata().rule_id): rule for rule in BUILT_IN_RULES}

    assert documented_rules.keys() == built_in_rules.keys()

    reference_source = RULE_REFERENCE_PATH.read_text(encoding="utf-8")
    for rule_id, rule in built_in_rules.items():
        metadata = rule.metadata()
        path, source = documented_rules[rule_id]
        expected_stem = rule.__module__.rsplit(".", maxsplit=1)[1]

        assert path.stem == expected_stem
        assert _string_export(source, "summary") == metadata.summary
        assert _string_export(source, "family") == metadata.family
        assert _bool_export(source, "defaultEnabled") is metadata.default_enabled
        assert all(heading in source for heading in REQUIRED_HEADINGS)
        assert source.count("```python") == 2
        assert reference_source.count(f"../rules/{expected_stem}.mdx") == 1


def _string_export(source: str, name: str) -> str:
    value = _export_value(source, name)
    parsed = ast.literal_eval(value)
    assert isinstance(parsed, str)
    return parsed


def _bool_export(source: str, name: str) -> bool:
    value = _export_value(source, name)
    assert value in {"false", "true"}
    return value == "true"


def _export_value(source: str, name: str) -> str:
    match = re.search(rf"^export const {name} = (.+)$", source, flags=re.MULTILINE)
    assert match is not None, f"missing {name} export"
    return match.group(1)
