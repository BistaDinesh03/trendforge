# TrendForge Setup

## 1. Virtual environment + install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pytest ruff bandit     # dev tools (also declared in pyproject.toml)
```

Python 3.12 is used in CI; local runs work on Python 3.11+.

## 2. Environment variables

Copy `.env.example` to `.env` (`.env` is git-ignored, never commit secrets):

| Variable | Required | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` | Recommended (required for reliable issue pulls) | GitHub API: license, topics, README, issues. Raises rate limits and keeps runs stable. |
| `OPENAI_API_KEY` | Optional | Enables the LLM analysis pass. Without it, TrendForge uses heuristic analysis. |
| `OPENAI_MODEL` | Optional | Defaults to `gpt-4o-mini`. |
| `TRENDFORGE_DRY_RUN` | Optional | `true` behaves like `--dry-run`. |
| `TRENDFORGE_MAX_ISSUES` | Optional | Max issues pulled per repo (default `60`). |

Get a token: GitHub → Settings → Developer settings → Personal access tokens
(classic or fine-grained, public read access is enough).

## 3. Run

```bash
python main.py --dry-run    # analyse + write reports/data/generated, no git push
python main.py              # full run: commits reports/, data/, generated/, README.md
```

A dry run prints `[dry-run] would commit: ...` instead of pushing.

## 4. Enable GitHub Actions

1. Repository → Settings → Secrets and variables → Actions → New repository
   secret → name `OPENAI_API_KEY` (optional; `GITHUB_TOKEN` is automatic).
2. Repository → Settings → Actions → General → Workflow permissions →
   **Read and write permissions** (the daily job commits reports back).
3. Actions tab → **Daily TrendForge** → **Run workflow** to trigger it manually
   once before trusting the 08:00 UTC schedule.

The workflow lives in `.github/workflows/daily.yml`
(`cron: 0 8 * * *` + `workflow_dispatch`). Dependabot keeps pip and
github-actions dependencies current (`.github/dependabot.yml`, weekly).

## 5. Output paths

| Path | Contents |
| --- | --- |
| `reports/YYYY-MM-DD.md` | Daily analysis report (indexed in `README.md`) |
| `data/snapshots.json` | Star/fork snapshots used to compute star velocity |
| `generated/YYYY-MM-DD-<slug>/` | Original scaffold for the day's idea |
| `.cache/` | 24-hour GitHub API response cache (git-ignored) |

## Quality gates

```bash
pytest -q           # unit tests
ruff check .        # lint (E, F, I, B, S/bandit, UP rules)
bandit -r trendforge main.py -lll   # high-severity security findings must be zero
```
