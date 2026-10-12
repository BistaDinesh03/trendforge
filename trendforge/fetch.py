"""Fetch GitHub Trending metadata and user complaints (metadata only, never code).

Network policy:
- every request has a timeout;
- every request is retried at most 3 times with exponential backoff;
- 403/429 responses back off and then surface as errors (no hammering);
- API responses are cached for 24 hours.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from github import Auth, Github, GithubException
from github.GithubRetry import GithubRetry
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from trendforge.config import Settings
from trendforge.models import Complaint, TrendingRepo

TRENDING_URL = "https://github.com/trending?since=daily"
API_BASE_URL = "https://api.github.com"
CACHE_TTL_SECONDS = 24 * 60 * 60
HTTP_TIMEOUT_SECONDS = 20
MAX_README_CHARS = 20_000
TOP_COMPLAINTS = 30

# Keyword map checked in CATEGORY_ORDER so specific themes win over generic ones.
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "security": (
        "security",
        "cve-",
        "vulnerab",
        "exploit",
        "injection",
        "xss",
        "csrf",
        "auth bypass",
        "credential leak",
    ),
    "docker": ("docker", "dockerfile", "container", "compose", "image build", "registry"),
    "windows": ("windows", "win32", "powershell", "cmd.exe", "wsl", "backslash"),
    "deps": (
        "dependencies",
        "dependency",
        "breaking change",
        "outdated",
        "version conflict",
        "requirements.txt",
        "package.json",
        "upgrade failed",
    ),
    "perf": ("performance", "slow", "latency", "memory leak", "cpu usage", "benchmark", "timeout"),
    "error": (
        "error",
        "exception",
        "traceback",
        "crash",
        "fails",
        "failed",
        "failure",
        "panic",
        "stacktrace",
        "boot",
        "segfault",
    ),
    "docs": ("documentation", "readme", "example", "typo", "unclear", "missing doc", "docs"),
    "setup": (
        "install",
        "setup",
        "set up",
        "getting started",
        "configure",
        "configuration",
        "prerequisite",
        "how do i",
        "first run",
    ),
}
CATEGORY_ORDER: tuple[str, ...] = (
    "security",
    "docker",
    "windows",
    "deps",
    "perf",
    "error",
    "docs",
    "setup",
)
DEFAULT_CATEGORY = "other"


class TrendingParseError(RuntimeError):
    """GitHub Trending HTML no longer matches our parser."""


def categorize(text: str) -> str:
    """Map free-form complaint text to one of the fixed complaint categories."""
    lowered = (text or "").lower()
    for category in CATEGORY_ORDER:
        for keyword in CATEGORY_KEYWORDS[category]:
            if keyword in lowered:
                return category
    return DEFAULT_CATEGORY


def _is_retryable_http_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {403, 408, 429, 500, 502, 503, 504}
    return False


retry_http = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception(_is_retryable_http_error),
    reraise=True,
)


def _parse_count(text: str) -> int:
    match = re.search(r"\d[\d,\.]*", text or "")
    if not match:
        return 0
    digits = re.sub(r"[^\d]", "", match.group(0))
    return int(digits) if digits else 0


@retry_http
def _get_text(url: str, *, headers: dict[str, str], params: dict[str, Any] | None = None) -> str:
    response = httpx.get(
        url,
        headers=headers,
        params=params,
        timeout=HTTP_TIMEOUT_SECONDS,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.text


@retry_http
def _get_json(url: str, *, headers: dict[str, str], params: dict[str, Any] | None = None) -> Any:
    response = httpx.get(
        url,
        headers=headers,
        params=params,
        timeout=HTTP_TIMEOUT_SECONDS,
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.json()


def parse_trending_html(html: str) -> TrendingRepo:
    """Parse the daily GitHub Trending page and return the #1 repository entry."""
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article.Box-row")
    if article is None:
        raise TrendingParseError(
            "GitHub Trending HTML changed: no <article class='Box-row'> entry found. "
            "Update trendforge.fetch.parse_trending_html selectors."
        )
    link = article.select_one("h2 a[href]")
    if link is None:
        raise TrendingParseError(
            "GitHub Trending HTML changed: no repository link (<h2><a>) in the entry."
        )
    href = str(link.get("href", "")).strip("/")
    parts = [part for part in href.split("/") if part]
    if len(parts) < 2:
        raise TrendingParseError(
            f"GitHub Trending HTML changed: unexpected repository href {href!r}."
        )
    owner, name = parts[0], parts[1]

    description_el = article.select_one("p")
    language_el = article.select_one('[itemprop="programmingLanguage"]')
    stars_today_el = article.select_one("span.d-inline-block.float-sm-right")

    total_stars = 0
    forks = 0
    for anchor in article.select("a.Link--muted"):
        anchor_href = str(anchor.get("href", ""))
        value = _parse_count(anchor.get_text(" ", strip=True))
        if anchor_href.endswith("/stargazers"):
            total_stars = value
        elif anchor_href.endswith("/forks"):
            forks = value

    return TrendingRepo(
        owner=owner,
        name=name,
        url=f"https://github.com/{owner}/{name}",
        description=description_el.get_text(" ", strip=True) if description_el else "",
        language=language_el.get_text(strip=True) if language_el else "",
        stars_today=_parse_count(stars_today_el.get_text(" ", strip=True)) if stars_today_el else 0,
        total_stars=total_stars,
        forks=forks,
    )


def fetch_top_trending(settings: Settings) -> TrendingRepo:
    """Download GitHub Trending (daily) and return the first repository listed."""
    html = _get_text(
        TRENDING_URL,
        headers={"User-Agent": settings.user_agent, "Accept": "text/html"},
    )
    return parse_trending_html(html)


# --------------------------------------------------------------------------- #
# Enrichment (license / topics / readme) via the GitHub API, cached for 24h.
# --------------------------------------------------------------------------- #


def _cache_file(cache_dir: Path, repo: TrendingRepo) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{repo.owner}--{repo.name}")
    return cache_dir / f"{safe}.json"


def _read_cache(cache_dir: Path, repo: TrendingRepo) -> TrendingRepo | None:
    try:
        payload = json.loads(_cache_file(cache_dir, repo).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    fetched_at = payload.get("fetched_at")
    if not isinstance(fetched_at, int | float):
        return None
    age = time.time() - float(fetched_at)
    if age < 0 or age > CACHE_TTL_SECONDS:
        return None
    try:
        return TrendingRepo.model_validate(payload.get("repo"))
    except (TypeError, ValueError):
        return None


def _write_cache(cache_dir: Path, repo: TrendingRepo) -> None:
    payload = {"fetched_at": int(time.time()), "repo": repo.model_dump(mode="json")}
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        _cache_file(cache_dir, repo).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        print(f"[trendforge] cache write skipped for {repo.full_name}")


def _github_client(settings: Settings) -> Github:
    return Github(
        auth=Auth.Token(settings.github_token),
        user_agent=settings.user_agent,
        timeout=HTTP_TIMEOUT_SECONDS,
        retry=GithubRetry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=(403, 408, 429, 500, 502, 503, 504),
        ),
    )


def _is_retryable_api_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, GithubException):
        return exc.status in {403, 408, 429, 500, 502, 503, 504}
    return False


api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception(_is_retryable_api_error),
    reraise=True,
)


@api_retry
def _fetch_repo_details(settings: Settings, repo: TrendingRepo) -> TrendingRepo:
    repository = _github_client(settings).get_repo(repo.full_name)
    license_spdx = ""
    license_name = ""
    topics: list[str] = []
    readme = ""
    try:
        license_obj = repository.license
        if license_obj is not None:
            license_spdx = str(license_obj.spdx_id or "")
            license_name = str(license_obj.name or "")
    except GithubException:
        print(f"[trendforge] license lookup failed for {repo.full_name}")
    try:
        topics = list(repository.topics or [])
    except GithubException:
        topics = []
    try:
        readme = repository.get_readme().decoded_content.decode("utf-8", "replace")
    except GithubException:
        readme = ""
    return repo.model_copy(
        update={
            "license_spdx": license_spdx,
            "license_name": license_name,
            "topics": topics,
            "readme": readme[:MAX_README_CHARS],
        }
    )


def enrich_with_api(settings: Settings, repo: TrendingRepo) -> TrendingRepo:
    """Fill license/topics/readme from the GitHub API; cache results for 24 hours."""
    cached = _read_cache(settings.cache_dir, repo)
    if cached is not None:
        print(f"[trendforge] cache hit: {repo.full_name}")
        return cached
    if not settings.github_token:
        print("[trendforge] no GITHUB_TOKEN set; skipping API enrichment")
        return repo
    try:
        enriched = _fetch_repo_details(settings, repo)
    except Exception as exc:
        print(f"[trendforge] API enrichment skipped: {type(exc).__name__}: {exc}")
        return repo
    _write_cache(settings.cache_dir, enriched)
    return enriched


# --------------------------------------------------------------------------- #
# Complaints: issue titles and metadata only, never issue bodies in full.
# --------------------------------------------------------------------------- #


def _reactions_from_raw(issue: Any) -> int:
    """Read the reaction total from the issue payload without extra API calls."""
    raw = getattr(issue, "_rawData", None)
    if isinstance(raw, dict):
        reactions = raw.get("reactions")
        if isinstance(reactions, dict) and isinstance(reactions.get("total_count"), int):
            return int(reactions["total_count"])
    return 0


@api_retry
def _issues_via_pygithub(settings: Settings, repo: TrendingRepo) -> list[dict[str, Any]]:
    repository = _github_client(settings).get_repo(repo.full_name)
    results: list[dict[str, Any]] = []
    for issue in repository.get_issues(state="open", sort="comments", direction="desc"):
        if len(results) >= settings.max_issues:
            break
        if getattr(issue, "pull_request", None) is not None:
            continue
        results.append(
            {
                "title": str(issue.title or ""),
                "body": str(issue.body or ""),
                "url": str(issue.html_url or ""),
                "comments": int(issue.comments or 0),
                "reactions": _reactions_from_raw(issue),
                "is_pr": False,
            }
        )
    return results


@api_retry
def _issues_via_rest(settings: Settings, repo: TrendingRepo) -> list[dict[str, Any]]:
    """Unauthenticated fallback: official REST API, one page, no scraping."""
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {
        "state": "open",
        "sort": "comments",
        "direction": "desc",
        "per_page": min(settings.max_issues, 100),
    }
    url = f"{API_BASE_URL}/repos/{repo.full_name}/issues"
    payload = _get_json(url, headers=headers, params=params)
    if not isinstance(payload, list):
        return []
    results: list[dict[str, Any]] = []
    for item in payload[: settings.max_issues]:
        reactions = item.get("reactions") or {}
        total_reactions = reactions.get("total_count") if isinstance(reactions, dict) else 0
        results.append(
            {
                "title": str(item.get("title") or ""),
                "body": str(item.get("body") or ""),
                "url": str(item.get("html_url") or ""),
                "comments": int(item.get("comments") or 0),
                "reactions": int(total_reactions or 0),
                "is_pr": "pull_request" in item,
            }
        )
    return results


def fetch_complaints(settings: Settings, repo: TrendingRepo) -> list[Complaint]:
    """Return the top 30 complaints (open issues) ranked by reactions + comments."""
    try:
        if settings.github_token:
            raw_issues = _issues_via_pygithub(settings, repo)
        else:
            raw_issues = _issues_via_rest(settings, repo)
    except Exception as exc:
        print(f"[trendforge] complaint fetch skipped: {type(exc).__name__}: {exc}")
        return []

    complaints: list[Complaint] = []
    for item in raw_issues:
        if item.get("is_pr"):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        body = str(item.get("body") or "")
        complaints.append(
            Complaint(
                source="issue",
                title=title,
                url=str(item.get("url") or ""),
                reactions=int(item.get("reactions") or 0),
                comments=int(item.get("comments") or 0),
                category=categorize(f"{title}\n{body}"),
            )
        )
    complaints.sort(key=lambda complaint: complaint.reactions + complaint.comments, reverse=True)
    return complaints[:TOP_COMPLAINTS]
