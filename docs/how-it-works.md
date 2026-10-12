# How it works

Five stages, one module each, orchestrated by `main.py`:

| Stage | Module | What happens |
| --- | --- | --- |
| 1. Fetch trending | `trendforge/fetch.py` | Parses the GitHub Trending page and takes the #1 repository |
| 2. Enrich | `trendforge/fetch.py` | License (SPDX id), topics, and README text via the GitHub API; cached for 24 hours in `.cache/` |
| 3. Complaints | `trendforge/fetch.py` | The 30 most-discussed open issues, ranked by reactions and comments |
| 4. Analyse | `trendforge/analyze.py`, `trendforge/llm.py` | License risk, complaint themes, trend reasons; optional OpenAI pass |
| 5. Forge | `trendforge/generate.py`, `trendforge/publish.py` | Original idea, daily report, 13-file scaffold, git commit |

## Data flow

| Path | Written by | Contents |
| --- | --- | --- |
| `data/snapshots.json` | `publish.py` | Star/fork samples per day; star velocity = (stars - previous stars) / elapsed days |
| `reports/YYYY-MM-DD.md` | `publish.py` | The daily markdown report |
| `generated/YYYY-MM-DD-<slug>/` | `generate.py` | The 13-file scaffold for the day's idea |
| `README.md` | `publish.py` | Report index between the `trendforge:reports` markers, refreshed in place |
| `.cache/` | `fetch.py` | 24-hour API response cache (git-ignored) |

## Rate limits and retries

HTTP calls retry with backoff on 403/429 (`tenacity`); the GitHub API client
uses `GithubRetry` with the same status list. One repository's enrichment is
fetched at most once per 24 hours.

## Scheduling

`.github/workflows/daily.yml` runs at 08:00 UTC (`cron: 0 8 * * *`) and on
`workflow_dispatch`. The job installs `requirements.txt`, runs
`python main.py`, then commits `reports/`, `data/`, `generated/`, and
`README.md` back to the repository. A local `python main.py` performs the same
commit and push from your machine.
