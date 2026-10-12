## What changed

<!-- One or two sentences. Close related issues with "Fixes #N". -->

## Checklist

- [ ] `python -m pytest -q` passes
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `mypy trendforge main.py` passes
- [ ] `bandit -r trendforge main.py -lll -q` reports nothing
- [ ] Docs updated if behavior changed
- [ ] No unrelated refactors; no secrets or `.env` files
