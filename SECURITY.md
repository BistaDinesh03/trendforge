# Security Policy

## Reporting a vulnerability

Please report security issues **privately**, using
[GitHub Security Advisories](https://github.com/BistaDinesh03/trendforge/security/advisories)
("Report a vulnerability") on this repository. Do not open a public issue for an
exploitable vulnerability. Include the affected component, a reproduction using
only public data, and the impact you observed.

## TrendForge specifics

- TrendForge runs daily in GitHub Actions (`.github/workflows/daily.yml`) with
  the built-in `GITHUB_TOKEN` and an optional `OPENAI_API_KEY` repository
  secret. Secrets are never written to code, reports, logs, or generated
  scaffolds.
- `.env` is git-ignored; `.env.example` contains placeholders only.
- TrendForge reads only **metadata, README text, issue titles, and discussion
  text** from other repositories - never source code - and every artifact it
  publishes (`reports/`, `data/`, `generated/`) is generated from that
  metadata by original code.
- No bots, no fake engagement, no trending manipulation of any kind: the
  pipeline is read-only with respect to other repositories.

## Supported versions

| Component           | Supported          |
| ------------------- | :----------------: |
| TrendForge (main)   | :white_check_mark: |
