"""Heuristic analysis: license risk, complaint themes, and trend reasons."""

from __future__ import annotations

from collections import Counter
from typing import Any

from trendforge.models import Complaint, LicenseRisk, TrendingRepo, TrendReasons

PERMISSIVE_LICENSES = frozenset(
    {
        "MIT",
        "Apache-2.0",
        "BSD",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "0BSD",
        "ISC",
        "MPL-2.0",
        "Unlicense",
        "CC0-1.0",
        "Zlib",
        "Python-2.0",
    }
)
COPYLEFT_LICENSES = frozenset(
    {
        "GPL-2.0",
        "GPL-3.0",
        "AGPL-3.0",
        "LGPL-2.1",
        "LGPL-3.0",
        "EUPL-1.2",
    }
)
COPYLEFT_PREFIXES = ("AGPL-", "GPL-", "LGPL-")
NO_LICENSE_VALUES = frozenset({"", "NONE", "NOASSERTION", "NO LICENSE", "UNLICENSED"})

PERMISSIVE_NOTES = (
    "Permissive license: reuse is allowed as long as the LICENSE text, copyright "
    "notice, and attribution are preserved (NOTICE file when the project ships one)."
)
COPYLEFT_NOTES = (
    "Copyleft license: any derivative work must ship under the same license. "
    "Keep copyright notices intact; we summarize and link, never copy code."
)
NO_LICENSE_NOTES = (
    "No license (or NOASSERTION): default copyright applies. Do not reuse any code; "
    "link to the repository and summarize only."
)
UNKNOWN_NOTES = (
    "Unrecognized license identifier: treat as no-reuse until the license is verified manually."
)
DEFAULT_THEME = "other"


def license_risk(spdx: str | None) -> LicenseRisk:
    """Classify an SPDX identifier into a reuse policy."""
    identifier = (spdx or "").strip()
    upper = identifier.upper()
    if upper in NO_LICENSE_VALUES:
        return LicenseRisk(spdx=identifier, level="none", can_reuse=False, notes=NO_LICENSE_NOTES)
    if identifier in PERMISSIVE_LICENSES or upper in PERMISSIVE_LICENSES:
        return LicenseRisk(
            spdx=identifier, level="permissive", can_reuse=True, notes=PERMISSIVE_NOTES
        )
    if identifier in COPYLEFT_LICENSES or upper.startswith(COPYLEFT_PREFIXES):
        return LicenseRisk(spdx=identifier, level="copyleft", can_reuse=True, notes=COPYLEFT_NOTES)
    return LicenseRisk(spdx=identifier, level="unknown", can_reuse=False, notes=UNKNOWN_NOTES)


def top_complaint_themes(complaints: list[Any], n: int = 10) -> list[tuple[str, int]]:
    """Rank complaint categories by frequency (most common first)."""
    counter: Counter[str] = Counter()
    for complaint in complaints:
        if isinstance(complaint, dict):
            category = complaint.get("category")
        else:
            category = getattr(complaint, "category", None)
        counter[str(category or DEFAULT_THEME)] += 1
    return counter.most_common(n)


def heuristic_trend_reasons(repo: TrendingRepo, complaints: list[Complaint]) -> TrendReasons:
    """Explain why the repository trended using signals only (no LLM)."""
    themes = top_complaint_themes(complaints, 3)
    if themes and complaints:
        top_name, top_count = themes[0]
        pain_point = (
            f"Recurring friction clusters around '{top_name}': {top_count} of "
            f"{len(complaints)} recent reports share that category."
        )
    else:
        pain_point = (
            "No complaint signal yet — momentum looks driven by novelty and visibility "
            "rather than a specific fixable pain point."
        )

    timing = (
        f"{repo.stars_today} stars today on top of {repo.total_stars} total stars "
        f"({repo.forks} forks): a spiky, time-sensitive burst worth riding now."
    )

    dx = repo.description or (
        "No description on the trending card; DX signal comes from topics: "
        f"{', '.join(repo.topics[:5]) or 'none listed'}."
    )

    theme_names = [name for name, _ in themes]
    if "docs" in theme_names:
        docs = "Docs gaps show up in reports: first-run guidance is a real weakness to fix."
    elif "setup" in theme_names:
        docs = "Setup friction dominates: onboarding docs and environment checks are the weak spot."
    else:
        docs = (
            "Docs are not the loudest complaint; the project is being discovered "
            "faster than it is being documented."
        )

    fork_rate = (repo.forks / repo.total_stars) if repo.total_stars else 0.0
    engagement = sum(complaint.reactions + complaint.comments for complaint in complaints)
    community = (
        f"Community signal: {repo.forks} forks against {repo.total_stars} stars "
        f"({fork_rate:.1%} fork rate) and {engagement} reactions/comments on recent issues."
    )

    summary = (
        f"{repo.owner}/{repo.name} ({repo.language or 'multi-language'}) trended with "
        f"{repo.stars_today} stars today. Strongest reported pain: "
        f"{themes[0][0] if themes else 'not yet measurable'}. "
        "We design an original tool around that pain — never a copy of this repository."
    )

    return TrendReasons(
        pain_point=pain_point,
        timing=timing,
        dx=dx,
        docs=docs,
        community=community,
        summary=summary,
    )
