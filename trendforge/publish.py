"""Persist snapshots, reports, the README index, and git publishing."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from trendforge.analyze import top_complaint_themes
from trendforge.config import TEMPLATES_DIR, Settings
from trendforge.models import DailyReport, Snapshot, TrendingRepo

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"
REPORTS_PATH = PROJECT_ROOT / "REPORTS.md"
SNAPSHOT_FILENAME = "snapshots.json"
GIT_TIMEOUT_SECONDS = 120
REPORTS_INDEX_START = "<!-- trendforge:reports:start -->"
REPORTS_INDEX_END = "<!-- trendforge:reports:end -->"


def record_snapshot(settings: Settings, repo: TrendingRepo, today: date) -> int:
    """Append today's star/fork sample and return stars-per-day since the last one."""
    path = settings.data_dir / SNAPSHOT_FILENAME
    snapshots = _load_snapshots(path)
    full_name = f"{repo.owner}/{repo.name}"
    previous = next((row for row in reversed(snapshots) if row.get("repo") == full_name), None)
    velocity = 0
    if previous is not None:
        try:
            previous_date = date.fromisoformat(str(previous.get("date")))
            raw_stars = previous.get("stars")
            previous_stars = int(raw_stars) if isinstance(raw_stars, (int, float)) else 0
            elapsed_days = max((today - previous_date).days, 1)
            velocity = round((repo.total_stars - previous_stars) / elapsed_days)
        except (TypeError, ValueError):
            velocity = 0
    snapshot = Snapshot(
        date=today.isoformat(),
        repo=full_name,
        stars=repo.total_stars,
        forks=repo.forks,
    )
    snapshots.append(snapshot.model_dump(mode="json"))
    _save_snapshots(path, snapshots)
    return velocity


def _load_snapshots(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(payload, list):
        return []
    return [row for row in payload if isinstance(row, dict)]


def _save_snapshots(path: Path, snapshots: list[dict[str, object]]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshots, indent=2) + "\n", encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"[trendforge] snapshot write failed: {exc}")


def write_report(settings: Settings, report: DailyReport) -> Path:
    """Render templates/report.md.j2 into reports/YYYY-MM-DD.md."""
    themes = top_complaint_themes(report.complaints, 10)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=False),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    rendered = env.get_template("report.md.j2").render(report=report, themes=themes)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    path = settings.reports_dir / f"{report.date}.md"
    path.write_text(rendered, encoding="utf-8", newline="\n")
    return path


def update_readme_index(settings: Settings) -> Path:
    """Refresh the report list between sentinels in README.md.

    Only the block between REPORTS_INDEX_START and REPORTS_INDEX_END is
    rewritten; the rest of the README stays untouched. When the sentinels are
    missing or reversed (for example on a fresh clone), the index is written
    to REPORTS.md instead and README.md is never modified.
    """
    report_paths = sorted(settings.reports_dir.glob("*.md"), reverse=True)
    if report_paths:
        index = "\n".join(f"- [{path.stem}](reports/{path.stem}.md)" for path in report_paths)
    else:
        index = "_No reports yet - run `python main.py --dry-run` to create one._"
    try:
        text = README_PATH.read_text(encoding="utf-8")
    except OSError:
        text = ""
    start = text.find(REPORTS_INDEX_START)
    end = text.find(REPORTS_INDEX_END)
    if start != -1 and end > start:
        prefix = text[: start + len(REPORTS_INDEX_START)]
        README_PATH.write_text(f"{prefix}\n{index}\n{text[end:]}", encoding="utf-8", newline="\n")
        return README_PATH
    REPORTS_PATH.write_text(f"# Reports\n\n{index}\n", encoding="utf-8", newline="\n")
    return REPORTS_PATH


def git_commit_and_push(settings: Settings, message: str) -> bool:
    """Commit reports/, data/, generated/ and README.md; never crash on push failure."""
    if settings.dry_run:
        print(f"[trendforge] [dry-run] would commit: {message}")
        return False
    git = shutil.which("git")
    if git is None:
        print("[trendforge] git executable not found; skipping publish")
        return False
    try:
        _ensure_identity(git)
        staged = ["reports", "data", "generated"]
        for extra in (README_PATH, REPORTS_PATH):
            if extra.exists():
                staged.append(extra.name)
        _git(git, ["add", *staged])
        committed = _git(git, ["commit", "-m", message])
        if committed.returncode != 0:
            print("[trendforge] nothing to commit (working tree unchanged)")
            return False
        pushed = _git(git, ["push"])
        if pushed.returncode != 0:
            print(f"[trendforge] git push failed: {pushed.stderr.strip()}")
            return False
        print("[trendforge] pushed to remote")
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[trendforge] git publish failed safely: {type(exc).__name__}: {exc}")
        return False


GIT_IDENTITY = (
    ("user.name", "TrendForge Bot"),
    ("user.email", "trendforge-bot@users.noreply.github.com"),
)


def _ensure_identity(git: str) -> None:
    """Set a local bot identity only when the repository has none configured."""
    for key, fallback in GIT_IDENTITY:
        current = _git(git, ["config", key])
        if current.returncode != 0 or not current.stdout.strip():
            _git(git, ["config", key, fallback])


def _git(git: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [git, *args],
        capture_output=True,
        text=True,
        shell=False,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
