# Contributing to TrendForge

Thanks for helping. This project ships original code only — **do not copy
source code from other repositories, trending or otherwise.** Metadata-inspired
ideas are fine; pasted code is not.

## Development setup

```bash
git clone https://github.com/BistaDinesh03/trendforge.git
cd trendforge
make setup          # requirements + dev tools (pytest, ruff, bandit, mypy)
make test
make lint && make type
```

Windows without `make`? Every target is a one-liner: `python -m pytest -q`,
`ruff check .`, `ruff format --check .`, `mypy trendforge main.py`,
`bandit -r trendforge main.py -lll -q`.

## Quality bar (all enforced in CI)

| Check | Command |
| --- | --- |
| Tests | `python -m pytest -q` |
| Lint | `ruff check .` (E,F,I,B,S,UP; line length 100) |
| Format | `ruff format --check .` |
| Types | `mypy trendforge main.py` |
| Security | `bandit -r trendforge main.py -lll -q` (0 high/medium) |

New behavior needs tests. Analysis heuristics need a test that pins the
decision (zero-judgment on the first three repositories, cache TTL, star
velocity math).

## Running the pipeline

```bash
python main.py --dry-run    # analyse + write reports/data/generated, no git push
```

`.env` holds optional secrets (`.env.example` lists them); `.env` is
git-ignored. Never commit tokens. See `SETUP.md` for environment variables.

## Pull requests

- One concern per PR; conventional-commit messages (`feat:`, `fix:`,
  `docs:`, `chore:`).
- CI must be green (lint, typecheck, tests, CodeQL).
- README claims must stay verifiable from code or a live URL — delete
  anything you cannot verify.
