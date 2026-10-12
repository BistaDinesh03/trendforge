PYTHON ?= python

.PHONY: setup run dry-run test lint type format

## setup: install dependencies + dev tools
setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install pytest ruff bandit mypy

## run: full pipeline (commits reports/, data/, generated/, README index)
run:
	$(PYTHON) main.py

## dry-run: analyse and write outputs without committing
dry-run:
	$(PYTHON) main.py --dry-run

## test: run the test suite
test:
	$(PYTHON) -m pytest -q

## lint: ruff lint + format check (same as CI)
lint:
	ruff check .
	ruff format --check .

## type: mypy over the package (same as CI)
type:
	mypy trendforge main.py

## format: autofix + rewrite files in place
format:
	ruff check --fix .
	ruff format .
