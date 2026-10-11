"""Tests for license risk classification and complaint theming."""

from trendforge.analyze import license_risk, top_complaint_themes
from trendforge.models import Complaint


def test_mit_is_permissive_and_reusable() -> None:
    risk = license_risk("MIT")
    assert risk.level == "permissive"
    assert risk.can_reuse is True


def test_missing_license_blocks_reuse() -> None:
    risk = license_risk("")
    assert risk.can_reuse is False
    assert risk.level == "none"


def test_noassertion_treated_as_no_license() -> None:
    risk = license_risk("NOASSERTION")
    assert risk.level == "none"
    assert risk.can_reuse is False


def test_gpl_is_copyleft_and_reusable_under_same_license() -> None:
    risk = license_risk("GPL-3.0")
    assert risk.level == "copyleft"
    assert risk.can_reuse is True


def test_top_complaint_themes_ranks_most_common_first() -> None:
    complaints = [
        Complaint(title="Install fails on fresh machine", category="setup"),
        Complaint(title="Cannot configure the tool", category="setup"),
        Complaint(title="Traceback on start", category="error"),
    ]
    themes = top_complaint_themes(complaints)
    assert themes[0] == ("setup", 2)


def test_top_complaint_themes_accepts_dicts() -> None:
    themes = top_complaint_themes([{"category": "docs"}, {"category": "docs"}])
    assert themes == [("docs", 2)]
