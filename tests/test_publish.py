"""Tests for the sentinel-scoped README report index."""

from pathlib import Path

import pytest

from trendforge import publish
from trendforge.config import Settings

START = publish.REPORTS_INDEX_START
END = publish.REPORTS_INDEX_END


def _settings_with_one_report(tmp_path: Path) -> Settings:
    reports = tmp_path / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "2026-10-11.md").write_text("# daily report\n", encoding="utf-8")
    return Settings(reports_dir=reports)


def test_update_readme_index_rewrites_only_sentinel_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        f"# TrendForge\n\nHand-written intro.\n\n{START}\nstale entry\n{END}\n\nTail section.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(publish, "README_PATH", readme)
    monkeypatch.setattr(publish, "REPORTS_PATH", tmp_path / "REPORTS.md")

    out = publish.update_readme_index(_settings_with_one_report(tmp_path))

    assert out == readme
    text = readme.read_text(encoding="utf-8")
    assert text.startswith("# TrendForge\n\nHand-written intro.\n")
    assert text.endswith("\n\nTail section.\n")
    assert "- [2026-10-11](reports/2026-10-11.md)" in text
    assert "stale entry" not in text
    assert not (tmp_path / "REPORTS.md").exists()


def test_update_readme_index_falls_back_to_reports_md(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    original = "# TrendForge\n\nNo sentinels here.\n"
    readme.write_text(original, encoding="utf-8")
    monkeypatch.setattr(publish, "README_PATH", readme)
    monkeypatch.setattr(publish, "REPORTS_PATH", tmp_path / "REPORTS.md")

    out = publish.update_readme_index(_settings_with_one_report(tmp_path))

    assert out == tmp_path / "REPORTS.md"
    assert readme.read_text(encoding="utf-8") == original
    fallback = out.read_text(encoding="utf-8")
    assert fallback.startswith("# Reports\n")
    assert "- [2026-10-11](reports/2026-10-11.md)" in fallback


def test_update_readme_index_empty_reports_dir_writes_placeholder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(f"{START}{END}\n", encoding="utf-8")
    monkeypatch.setattr(publish, "README_PATH", readme)
    monkeypatch.setattr(publish, "REPORTS_PATH", tmp_path / "REPORTS.md")
    (tmp_path / "reports").mkdir()

    out = publish.update_readme_index(Settings(reports_dir=tmp_path / "reports"))

    text = out.read_text(encoding="utf-8")
    assert "No reports yet" in text
    assert out == readme
