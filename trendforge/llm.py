"""Optional LLM analysis.

Uses OpenAI when OPENAI_API_KEY is set; returns (None, None) on any failure so the
pipeline can fall back to heuristics. This module must never crash a run.
"""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from trendforge.config import Settings
from trendforge.models import Complaint, ProjectIdea, TrendingRepo, TrendReasons

SYSTEM_PROMPT = (
    "You are a product strategist for open-source. Return STRICT JSON only. "
    "Never suggest copying another repo's code. All output must be original."
)

# Schema the model must produce (documented inline as required by json_object mode).
JSON_SCHEMA_DOC = """{
  "trend_reasons": {
    "pain_point": "string - the core user pain driving interest",
    "timing": "string - why this is trending now",
    "dx": "string - developer-experience observations",
    "docs": "string - documentation observations",
    "community": "string - community/activity observations",
    "summary": "string - 2-3 sentence explanation of the trend"
  },
  "project_idea": {
    "slug": "string - lowercase-with-dashes, original, 2-4 words",
    "name": "string - original project name (must not exist on GitHub)",
    "tagline": "string - one line value proposition",
    "problem": "string - the concrete problem it solves",
    "target_users": "string - who it is for",
    "mvp_features": ["string - 4-6 MVP features"],
    "stack": ["string - 3-5 technology choices"],
    "seven_day_plan": ["string - 7 entries, one per day"],
    "monetization": ["string - 2-4 honest open-source monetization paths"],
    "launch_plan": ["string - 3-5 launch steps (no spam, no fake stars, no bots)"]
  }
}"""


def build_user_prompt(
    repo: TrendingRepo,
    themes: list[tuple[str, int]],
    complaints: list[Complaint],
) -> str:
    """Assemble the analysis prompt from metadata, themes, and complaint titles."""
    theme_lines = "\n".join(f"- {name}: {count}" for name, count in themes) or "- none"
    complaint_lines = "\n".join(
        f"- [{item.category}] {item.title} "
        f"({item.comments} comments, {item.reactions} reactions) {item.url}"
        for item in complaints[:12]
    ) or "- none"
    return f"""Repo metadata (metadata only, no code was read):
- full name: {repo.owner}/{repo.name}
- url: {repo.url}
- description: {repo.description}
- language: {repo.language}
- stars today / total / forks: {repo.stars_today} / {repo.total_stars} / {repo.forks}
- license: {repo.license_spdx or 'unknown'}
- topics: {', '.join(repo.topics) or 'none'}

Top complaint themes (category: count):
{theme_lines}

Top complaint titles:
{complaint_lines}

Respond with STRICT JSON following exactly this schema:
{JSON_SCHEMA_DOC}

Rules:
- All names, ideas, and wording must be original; never propose copying code,
  architecture, README text, or naming from the trending repository.
- The project idea must directly address the loudest complaint themes.
- Launch plan must be honest growth only: no fake stars, no bots, no spam.
"""


def _parse_json(content: str) -> dict[str, Any] | None:
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except ValueError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            payload = json.loads(match.group(0))
        except ValueError:
            return None
    return payload if isinstance(payload, dict) else None


def analyze_with_llm(
    settings: Settings,
    repo: TrendingRepo,
    themes: list[tuple[str, int]],
    complaints: list[Complaint],
) -> tuple[TrendReasons | None, ProjectIdea | None]:
    """Return LLM-written (trend reasons, project idea), or (None, None) on failure."""
    if not settings.openai_api_key:
        print("[trendforge] no OPENAI_API_KEY set; using heuristic analysis")
        return None, None
    try:
        client = OpenAI(api_key=settings.openai_api_key, timeout=60.0, max_retries=2)
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(repo, themes, complaints)},
            ],
        )
        content = response.choices[0].message.content or ""
        payload = _parse_json(content)
        if payload is None:
            print("[trendforge] LLM returned non-JSON output; using heuristics")
            return None, None
        reasons = _build_trend_reasons(payload.get("trend_reasons"))
        idea = _build_project_idea(payload.get("project_idea"))
        if reasons is None and idea is None:
            print("[trendforge] LLM JSON did not match the schema; using heuristics")
        return reasons, idea
    except Exception as exc:
        print(f"[trendforge] LLM analysis failed ({type(exc).__name__}); using heuristics")
        return None, None


def _build_trend_reasons(raw: Any) -> TrendReasons | None:
    if not isinstance(raw, dict):
        return None
    try:
        return TrendReasons.model_validate(raw)
    except (TypeError, ValueError):
        return None


def _build_project_idea(raw: Any) -> ProjectIdea | None:
    if not isinstance(raw, dict):
        return None
    try:
        idea = ProjectIdea.model_validate(raw)
    except (TypeError, ValueError):
        return None
    if not idea.slug or not idea.name:
        return None
    return idea
