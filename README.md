# TrendForge

**Every day at 08:00 UTC, TrendForge studies the #1 GitHub Trending repository -
metadata only - and forges an ORIGINAL open-source project that solves what
users actually complain about.**

## What TrendForge does

1. Reads the daily GitHub Trending page and takes the #1 repository.
2. Enriches it through the official GitHub API (license, topics, README text;
   cached 24h, rate-limit aware, backs off on 403/429).
3. Pulls the most-discussed open issues and categorizes the complaints.
4. Explains *why* it trended (heuristics, plus an optional LLM pass).
5. Designs an original project idea, writes a daily report, scaffolds the
   project, and pushes everything back to GitHub.

## Safety

- **TrendForge never copies source code.** We only read metadata, README text,
  issues, PRs, and discussions - never another repository's code.
- Licenses are respected: permissive licenses allow reuse *with attribution*
  (LICENSE, copyright, NOTICE preserved), copyleft keeps the same license, and
  no-license repositories are link-and-summarize only.
- No fake stars, no bots, no trending manipulation, no spam - ever.
- All output is original: names, code, architecture, README, and docs.

## Reports index

- [2026-10-11](reports/2026-10-11.md)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # set GITHUB_TOKEN; OPENAI_API_KEY is optional
python main.py --dry-run           # analyse + write files, no git push
python main.py                     # full run, commits and pushes
```

Daily automation lives in `.github/workflows/daily.yml` (08:00 UTC). See
[SETUP.md](SETUP.md) for the full setup guide.

## Repository layout

- `reports/` - daily analysis reports (this index is rebuilt each run)
- `data/snapshots.json` - star/fork history used for star velocity
- `generated/` - original project scaffolds, one per day
- `trendforge/` - the pipeline (fetch, analyze, llm, generate, publish)
- `templates/` - Jinja2 templates for reports and scaffold READMEs

## License

MIT - see [LICENSE](LICENSE).
