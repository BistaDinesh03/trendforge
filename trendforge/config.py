"""Environment-driven configuration for TrendForge."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_USER_AGENT = "TrendForge/1.0 (+https://github.com/trendforge/trendforge)"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


class Settings(BaseModel):
    """Runtime settings resolved from environment variables."""

    github_token: str = Field(default="", description="GitHub token used for API calls.")
    openai_api_key: str = Field(default="", description="OpenAI API key (optional).")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model id.")
    user_agent: str = Field(default=DEFAULT_USER_AGENT, description="User-Agent for HTTP calls.")
    dry_run: bool = Field(default=False, description="Analyse and write files, but never push.")
    cache_dir: Path = Field(default=Path(".cache"), description="24h API response cache.")
    data_dir: Path = Field(default=Path("data"), description="Snapshot history directory.")
    reports_dir: Path = Field(default=Path("reports"), description="Daily markdown reports.")
    generated_dir: Path = Field(default=Path("generated"), description="Generated scaffolds.")
    max_issues: int = Field(default=60, ge=1, le=300, description="Max issues per repo.")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_settings(dry_run: bool = False) -> Settings:
    """Read settings from the environment and create the working directories."""
    env_dry_run = os.getenv("TRENDFORGE_DRY_RUN", "").strip().lower() in TRUE_VALUES
    settings = Settings(
        github_token=os.getenv("GITHUB_TOKEN", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini",
        user_agent=os.getenv("TRENDFORGE_USER_AGENT", "").strip() or DEFAULT_USER_AGENT,
        dry_run=dry_run or env_dry_run,
        cache_dir=Path(os.getenv("TRENDFORGE_CACHE_DIR", "").strip() or ".cache"),
        data_dir=Path(os.getenv("TRENDFORGE_DATA_DIR", "").strip() or "data"),
        reports_dir=Path(os.getenv("TRENDFORGE_REPORTS_DIR", "").strip() or "reports"),
        generated_dir=Path(os.getenv("TRENDFORGE_GENERATED_DIR", "").strip() or "generated"),
        max_issues=_env_int("TRENDFORGE_MAX_ISSUES", 60),
    )
    working_dirs = (
        settings.cache_dir,
        settings.data_dir,
        settings.reports_dir,
        settings.generated_dir,
    )
    for directory in working_dirs:
        directory.mkdir(parents=True, exist_ok=True)
    return settings
