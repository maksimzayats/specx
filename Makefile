.PHONY: check list-skills validate-skills

check: validate-skills list-skills

validate-skills:
	uv run --with pyyaml python scripts/validate_skills.py skills

list-skills:
	npx skills add . --list --full-depth
