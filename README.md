<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
    <img src="assets/banner.svg" alt="TrendForge - daily GitHub Trending analysis that forges an original project" width="100%">
  </picture>
</p>

<p align="center">
  <strong>Every day at 08:00 UTC, TrendForge studies the #1 GitHub Trending repository - metadata only - and scaffolds an original open-source project.</strong>
</p>

<p align="center">
  <a href="https://github.com/BistaDinesh03/trendforge/actions/workflows/ci.yml"><img src="https://github.com/BistaDinesh03/trendforge/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/BistaDinesh03/trendforge/actions/workflows/codeql.yml"><img src="https://github.com/BistaDinesh03/trendforge/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-2563EB" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-MIT-2563EB" alt="License: MIT">
  <img src="https://img.shields.io/badge/ruff-checked-2563EB" alt="Ruff checked">
  <img src="https://img.shields.io/badge/bandit-pass-16A34A" alt="Bandit pass">
</p>

<p align="center">
  <a href="#reports">Reports</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="docs/index.md">Docs</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

## The problem

GitHub Trending lists what is popular today. It does not explain why something
trended, which complaints users repeat, or what a good next project would be.
Checking the page by hand does not scale, and reusing another repository's
source code would miss the point - TrendForge's output must be original.

## What TrendForge does

1. `trendforge/fetch.py` reads the daily GitHub Trending page and takes the #1
   repository.
2. It enriches that entry through the official GitHub API - license, topics,
   README text - cached for 24 hours, with retries on 403/429.
3. It pulls the 30 most-discussed open issues, ranked by reactions and
   comments, and categorizes the complaints.
4. It explains why the project trended with heuristics; when `OPENAI_API_KEY`
   is set, an LLM pass refines the analysis (`trendforge/llm.py`).
5. It designs an original project idea, writes the daily report, scaffolds the
   project under `generated/`, and commits the results.

The pipeline runs daily from `.github/workflows/daily.yml` (cron `0 8 * * *`)
and can run locally with `python main.py --dry-run`. Stage-by-stage details:
[docs/how-it-works.md](docs/how-it-works.md).

## Reports

Each run appends a dated report and refreshes this index between the markers
below. Automation never touches any other part of this README:

<!-- trendforge:reports:start -->
- [2026-10-11](reports/2026-10-11.md)
<!-- trendforge:reports:end -->

## Quickstart

```bash
git clone https://github.com/BistaDinesh03/trendforge.git
cd trendforge
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # GITHUB_TOKEN recommended; OPENAI_API_KEY optional
python main.py --dry-run
```

A dry run analyses the trending repository and writes `reports/`, `data/`, and
`generated/` without touching git. `python main.py` additionally commits and
pushes those results. Full setup (including GitHub Actions): [SETUP.md](SETUP.md).

## Commands

| Command | What it does |
| --- | --- |
| `python main.py --dry-run` | Full pipeline; writes files, never commits |
| `python main.py` | Full pipeline; commits `reports/`, `data/`, `generated/`, and the report index |
| `make setup` | Install requirements and dev tools (pytest, ruff, bandit, mypy) |
| `make test` | `python -m pytest -q` |
| `make lint` | `ruff check .` and `ruff format --check .` |
| `make type` | `mypy trendforge main.py` |
| `make format` | Autofix lint findings and rewrite formatting in place |

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` | Recommended | GitHub API access: license, topics, README, issues |
| `OPENAI_API_KEY` | Optional | Enables the LLM analysis pass; without it, heuristics run |
| `OPENAI_MODEL` | Optional | Model id (default `gpt-4o-mini`) |
| `TRENDFORGE_DRY_RUN` | Optional | `true` behaves like `--dry-run` |
| `TRENDFORGE_MAX_ISSUES` | Optional | Issues pulled per repository (default `60`) |

`.env` is git-ignored; `.env.example` contains placeholders only.

## What the generated project includes

Every `generated/YYYY-MM-DD-<slug>/` directory is a self-contained scaffold:

- `README.md` - problem, MVP features, tech stack, 7-day plan, launch plan
- `LICENSE` (MIT), `SECURITY.md`, `CONTRIBUTING.md`
- `pyproject.toml`, `Makefile`, `Dockerfile`, `.gitignore`, `.env.example`
- `.github/dependabot.yml`
- `src/<package>/__init__.py` and `src/<package>/main.py`
- `tests/test_smoke.py`

[`generated/2026-10-11-forgefix/`](generated/2026-10-11-forgefix/) is the
first real output. To take a scaffold to a public repository, follow
[docs/launch-checklist.md](docs/launch-checklist.md); to keep it healthy,
[docs/health-checklist.md](docs/health-checklist.md).

## Safety rules

- TrendForge reads **metadata, README text, and open issues** - never source
  code from other repositories.
- Every artifact it writes (`reports/`, `data/`, `generated/`) is produced by
  this repository's own code from that metadata.
- No bots, no fake stars, no trending manipulation: the pipeline is read-only
  with respect to other repositories.
- Each report classifies the analysed repository's license risk (permissive,
  copyleft, or none).

## Documentation

- [docs/index.md](docs/index.md) - start here
- [docs/how-it-works.md](docs/how-it-works.md) - pipeline stages and data flow
- [docs/launch-checklist.md](docs/launch-checklist.md) - launch a generated project
- [docs/health-checklist.md](docs/health-checklist.md) - keep a generated project healthy
- [SETUP.md](SETUP.md) - local and GitHub Actions setup

To browse the docs as a site: `pip install mkdocs && mkdocs serve`.

## Contributing

Setup, quality gates, and pull-request rules: [CONTRIBUTING.md](CONTRIBUTING.md).
Code of conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE) (c) TrendForge contributors. Original code only - repository
metadata reads never result in copied source.

---

Built with httpx, PyGithub, BeautifulSoup, Pydantic, and Jinja2.

## Contributors

- [@BistaDinesh03](https://github.com/BistaDinesh03) - maintainer

<!-- Hand-maintained, human-only list on purpose. A dynamic contributor image
     (contrib.rocks / all-contributors) also renders bot accounts -
     dependabot[bot], github-actions[bot], github-advanced-security[bot] -
     which are automation, not people. Add humans here by hand. -->
