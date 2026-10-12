# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-11

### Added

- Daily pipeline (`.github/workflows/daily.yml`, cron `0 8 * * *` plus
  `workflow_dispatch`): fetch the #1 GitHub Trending repository, analyse it,
  and commit `reports/` + `data/snapshots.json` back to the repository
- `python main.py --dry-run`: full pipeline with no git commit or push
- 24-hour HTTP response cache with retries and backoff on 403/429
  (`trendforge/fetch.py`)
- Heuristic analysis that runs without any API key; optional OpenAI pass
  when `OPENAI_API_KEY` is set (`trendforge/llm.py`)
- Daily markdown report with star velocity and issue themes
  (`trendforge/publish.py`)
- Original project scaffold under `generated/` (13 files: README, MIT
  license, SECURITY, CONTRIBUTING, Dockerfile, Makefile, package, smoke test)
- README report index

[Unreleased]: https://github.com/BistaDinesh03/trendforge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/BistaDinesh03/trendforge/releases/tag/v0.1.0
