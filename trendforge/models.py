"""Pydantic v2 models shared across the TrendForge pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrendingRepo(BaseModel):
    """Metadata for the repository at the top of GitHub Trending."""

    owner: str = ""
    name: str = ""
    url: str = ""
    description: str = ""
    language: str = ""
    stars_today: int = 0
    total_stars: int = 0
    forks: int = 0
    license_spdx: str = ""
    license_name: str = ""
    topics: list[str] = Field(default_factory=list)
    readme: str = ""

    @property
    def full_name(self) -> str:
        """Return the owner/name slug used by the GitHub API."""
        return f"{self.owner}/{self.name}"


class Complaint(BaseModel):
    """One user complaint (issue title + metadata). We never store source code."""

    source: str = "issue"
    title: str = ""
    url: str = ""
    reactions: int = 0
    comments: int = 0
    category: str = "other"


class LicenseRisk(BaseModel):
    """How safely we may reuse ideas (never code) from a repository."""

    spdx: str = ""
    level: str = "unknown"  # permissive | copyleft | none | unknown
    can_reuse: bool = False
    notes: str = ""


class TrendReasons(BaseModel):
    """Heuristic or LLM-written explanation of why the repository trended."""

    pain_point: str = ""
    timing: str = ""
    dx: str = ""
    docs: str = ""
    community: str = ""
    summary: str = ""


class ProjectIdea(BaseModel):
    """An original project concept designed from the observed complaints."""

    slug: str = "forgefix"
    name: str = "ForgeFix"
    tagline: str = ""
    problem: str = ""
    target_users: str = ""
    mvp_features: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    seven_day_plan: list[str] = Field(default_factory=list)
    monetization: list[str] = Field(default_factory=list)
    launch_plan: list[str] = Field(default_factory=list)


class Snapshot(BaseModel):
    """A daily star/fork sample used to compute star velocity."""

    date: str = ""
    repo: str = ""
    stars: int = 0
    forks: int = 0


class DailyReport(BaseModel):
    """Everything published for one day."""

    date: str = ""
    repo: TrendingRepo = Field(default_factory=TrendingRepo)
    complaints: list[Complaint] = Field(default_factory=list)
    license_risk: LicenseRisk = Field(default_factory=LicenseRisk)
    trend_reasons: TrendReasons = Field(default_factory=TrendReasons)
    idea: ProjectIdea = Field(default_factory=ProjectIdea)
    star_velocity: int = 0
