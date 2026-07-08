.PHONY: build check format lint list-skills test type validate-skills verifytypes

check: lint type test build verifytypes validate-skills list-skills

format:
	uv run ruff check --fix src tests scripts
	uv run ruff format src tests scripts

lint:
	uv run ruff check src tests scripts
	uv run ruff format --check src tests scripts

type:
	uv run mypy src tests scripts
	uv run pyright

test:
	uv run pytest

build:
	uv build --no-sources

verifytypes: build
	@wheel="$$(ls -t dist/specx-*.whl | head -n 1)"; \
	uv run --with "$$wheel" --with pyright pyright --verifytypes specx --ignoreexternal

validate-skills:
	uv run --with pyyaml python scripts/validate_skills.py skills

list-skills:
	npx skills add . --list --full-depth
