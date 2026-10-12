# TrendForge documentation

TrendForge analyses the #1 GitHub Trending repository every day - metadata
only - and scaffolds an original open-source project from what it learns.

| Doc | Contents |
| --- | --- |
| [How it works](how-it-works.md) | Pipeline stages, caching, and data flow |
| [Launch checklist](launch-checklist.md) | Take a generated scaffold to a public repository |
| [Health checklist](health-checklist.md) | Keep a generated project healthy |

Setup (environment variables, GitHub Actions, branch protection):
[SETUP.md](../SETUP.md). Contributing: [CONTRIBUTING.md](../CONTRIBUTING.md).

## Run it locally

```bash
pip install -r requirements.txt
python main.py --dry-run
```

Reports land in [`reports/`](../reports/); generated projects land in
[`generated/`](../generated/). Browse this documentation as a site with
`pip install mkdocs && mkdocs serve`.
