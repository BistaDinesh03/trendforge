"""Tests for complaint categorization and trending-page parsing."""

import pytest

from trendforge.fetch import TrendingParseError, categorize, parse_trending_html


def test_categorize_setup_question() -> None:
    assert categorize("How do I install this?") == "setup"


def test_categorize_error_report() -> None:
    assert categorize("Traceback: app fails to boot") == "error"


def test_categorize_uncategorized_praise() -> None:
    assert categorize("Nice project!") == "other"


def test_categorize_prefers_specific_theme() -> None:
    assert categorize("Docker container crashes with a setup error") == "docker"


MINIMAL_TRENDING_HTML = """
<html><body>
<article class="Box-row">
  <h2><a href="/octocat/sample-app">sample-app</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">A sample description of the repo.</p>
  <span itemprop="programmingLanguage">Python</span>
  <a class="Link--muted" href="/octocat/sample-app/stargazers">1,234</a>
  <a class="Link--muted" href="/octocat/sample-app/forks">56</a>
  <span class="d-inline-block float-sm-right">999 stars today</span>
</article>
</body></html>
"""


def test_parse_trending_html_extracts_repository() -> None:
    repo = parse_trending_html(MINIMAL_TRENDING_HTML)
    assert repo.owner == "octocat"
    assert repo.name == "sample-app"
    assert repo.url == "https://github.com/octocat/sample-app"
    assert repo.description == "A sample description of the repo."
    assert repo.language == "Python"
    assert repo.stars_today == 999
    assert repo.total_stars == 1234
    assert repo.forks == 56


def test_parse_trending_html_raises_when_structure_changes() -> None:
    with pytest.raises(TrendingParseError):
        parse_trending_html("<html><body><p>redesigned page</p></body></html>")
