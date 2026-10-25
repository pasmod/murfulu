PY ?= .venv/bin/python
NPM ?= npm --prefix web

.PHONY: install check lint types test format hooks web-install web-check web-format check-all

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check src tests tools migrations
	$(PY) -m ruff format --check src tests tools migrations

types:
	$(PY) -m mypy

test:
	$(PY) -m pytest

check: lint types test

format:
	$(PY) -m ruff format src tests tools migrations
	$(PY) -m ruff check --fix src tests tools migrations

# The pre-commit check that keeps the host's specifics, credentials and
# people's names out of this public repository (tools/public_check.py). The
# terms themselves go in .denylist, which is local: copy .denylist.example.
hooks:
	git config core.hooksPath tools/hooks
	@test -f .denylist || echo "no .denylist yet: copy .denylist.example and fill it in"

# The frontend is checked with its own toolchain. It is a separate target
# rather than part of `check`, so the backend still checks on a machine with
# no Node installed. `check-all` runs both.
web-install:
	$(NPM) ci

web-check:
	$(NPM) run check

web-format:
	$(NPM) run lint -- --fix

check-all: check web-check
