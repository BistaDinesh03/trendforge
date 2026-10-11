"""TrendForge CLI: analyse today's #1 trending repo and forge an original project.

Pipeline:
fetch trending -> API enrichment -> complaints -> themes -> license risk ->
heuristic reasons -> fallback idea -> optional LLM override -> snapshot ->
scaffold -> report -> README index -> git publish.
"""

from __future__ import annotations

import argparse
import traceback
from datetime import UTC, datetime

from dotenv import load_dotenv

from trendforge.analyze import heuristic_trend_reasons, license_risk, top_complaint_themes
from trendforge.config import load_settings
from trendforge.fetch import enrich_with_api, fetch_complaints, fetch_top_trending
from trendforge.generate import generate_scaffold
from trendforge.llm import analyze_with_llm
from trendforge.models import DailyReport, ProjectIdea
from trendforge.publish import (
    git_commit_and_push,
    record_snapshot,
    update_readme_index,
    write_report,
)


def _log(message: str) -> None:
    print(f"[trendforge] {message}", flush=True)


def forgefix_idea() -> ProjectIdea:
    """Fallback original idea: one command setup + health checks for any OSS project."""
    return ProjectIdea(
        slug="forgefix",
        name="ForgeFix",
        tagline="One command to set up, health-check, and repair any open-source project.",
        problem=(
            "Every repository reinvents onboarding. Newcomers hit broken setup steps, missing "
            "environment checks, and no fast signal about what is unhealthy, so maintainers "
            "answer the same setup and error questions forever."
        ),
        target_users=(
            "Developers evaluating or adopting an unfamiliar open-source project, and the "
            "maintainers who support them."
        ),
        mvp_features=[
            "`forgefix init` - detect the stack (Python, Node, Go, Docker) and write a "
            "checked-in setup plan",
            "`forgefix doctor` - environment, dependency, and config checks with clear "
            "pass/fail output",
            "`forgefix up` - one-command bootstrap: toolchains, dependencies, services, seed data",
            "`forgefix report` - machine-readable health report (JSON) plus a summary that "
            "issue templates can embed",
            "Plugin hooks so maintainers add project-specific checks without forking",
        ],
        stack=[
            "Python 3.12 + Typer CLI",
            "httpx for service probes, Pydantic v2 for check schemas",
            "GitHub Action wrapper for continuous health reporting",
        ],
        seven_day_plan=[
            "Day 1: CLI skeleton, config format, check registry",
            "Day 2: stack detection plus Python project checks",
            "Day 3: Node and Docker checks",
            "Day 4: doctor reporting, JSON output, exit codes",
            "Day 5: idempotent `up` bootstrap runner",
            "Day 6: docs, examples, sample plugins, tests",
            "Day 7: launch prep - README, demo GIF, first tagged release",
        ],
        monetization=[
            "Free core CLI under MIT; hosted team dashboard on a freemium tier",
            "Sponsored presets for popular frameworks and CI templates",
        ],
        launch_plan=[
            "Publish the problem statement and a 60s demo on dev.to and Show HN",
            "Release a launch-week checklist as a GitHub template repository",
            "Triage 'plugin request' issues weekly and ship visible improvements",
        ],
    )


def run(args: argparse.Namespace) -> int:
    """Execute the full daily pipeline. Returns a process exit code."""
    settings = load_settings(dry_run=args.dry_run)
    mode = "dry-run" if settings.dry_run else "live"
    _log(f"starting ({mode} mode)")

    _log("fetching #1 daily trending repository")
    repo = fetch_top_trending(settings)
    _log(f"trending: {repo.owner}/{repo.name} (+{repo.stars_today} stars today)")

    repo = enrich_with_api(settings, repo)
    _log(f"enriched: license={repo.license_spdx or 'unknown'} topics={len(repo.topics)}")

    complaints = fetch_complaints(settings, repo)
    _log(f"complaints: {len(complaints)} ranked issues")

    themes = top_complaint_themes(complaints)
    theme_summary = ", ".join(f"{name}({count})" for name, count in themes[:3]) or "none"
    _log(f"top themes: {theme_summary}")

    risk = license_risk(repo.license_spdx)
    _log(f"license risk: {risk.level} (reuse allowed: {risk.can_reuse})")

    reasons = heuristic_trend_reasons(repo, complaints)
    idea = forgefix_idea()
    _log(f"heuristic idea fallback: {idea.name} ({idea.slug})")

    llm_reasons, llm_idea = analyze_with_llm(settings, repo, themes, complaints)
    if llm_reasons is not None:
        reasons = llm_reasons
        _log("trend reasons: LLM")
    else:
        _log("trend reasons: heuristics")
    if llm_idea is not None:
        idea = llm_idea
        _log(f"project idea (LLM): {idea.name} ({idea.slug})")
    else:
        _log(f"project idea (fallback): {idea.name} ({idea.slug})")

    today = datetime.now(UTC).date()
    velocity = record_snapshot(settings, repo, today)
    _log(f"star velocity: {velocity} stars/day")

    report = DailyReport(
        date=today.isoformat(),
        repo=repo,
        complaints=complaints,
        license_risk=risk,
        trend_reasons=reasons,
        idea=idea,
        star_velocity=velocity,
    )

    scaffold_dir = generate_scaffold(settings, report)
    _log(f"scaffold: {scaffold_dir}")

    report_path = write_report(settings, report)
    _log(f"report: {report_path}")

    update_readme_index(settings)
    _log("README index updated")

    git_commit_and_push(
        settings,
        message=f"trendforge: {report.date} - {repo.owner}/{repo.name} -> {idea.slug}",
    )
    _log("done")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        prog="trendforge",
        description="Analyse the #1 GitHub Trending repo and forge an original project.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="analyse and write all outputs without committing or pushing",
    )
    args = parser.parse_args(argv)
    load_dotenv()
    try:
        return run(args)
    except Exception as exc:
        _log(f"ERROR: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
