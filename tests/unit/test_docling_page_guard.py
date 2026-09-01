"""Pins the page-selection guard added for inbox 20260831T0700Z.

Three distinct failure forms were measured on the 2026.2Q round:

  A  the required section's page was never selected (keyword window evicted it)
  B  the section's table reached the MD only in part
  C  the page WAS selected and appeared in ``keyword_hit_pages``, yet the page's
     content silently vanished from the markdown

Before this guard nothing read the front matter or checked the converted body,
so all three read downstream as "the filer did not disclose it".

**2026-09-01 rewrite.** An earlier round exposed a `page_selection_flags()`
helper and this file tested it directly. The guard was then rebuilt against a
39-company calibration and folded into `score()` — checking the **converted
body** rather than the page-range arithmetic, because the ratio signal turned
out to have no discriminative power (normal and defective filings overlap
heavily) while the section markers separate cleanly. Testing the body is also
strictly better: it catches form A *and* form C, since both end with the
section absent from the markdown regardless of why.

These tests now pin the surviving contract: even quarters require the section
markers, odd quarters are exempt (간이공시 cadence, not a parser gap), and the
ratio floor stays a low catastrophic-failure net rather than a primary signal.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solvency.parser import quality_check as QC  # noqa: E402

MARKET_BODY = (
    "6-4. 시장위험 관리\n금리위험액 1,234\n주식위험액 567\n부동산위험액 89\n"
    "외환위험액 12\n자산집중위험액 3\n"
)
SENSITIVITY_BODY = "6-8. 위험민감도\n금리 민감도 분석 표\n"
FULL_BODY = MARKET_BODY + SENSITIVITY_BODY


def _meta(quarter: str = "Q2", spr: str = "4-40", total: str = "60") -> dict[str, str]:
    return {
        "period": f"FY2026_{quarter}",
        "quarter": quarter,
        "parse_scope": "keyword_window",
        "source_page_ranges": spr,
        "source_total_pages": total,
    }


# --------------------------------------------------------------------- markers
def test_full_body_has_no_missing_section_rows() -> None:
    assert QC._missing_rows(FULL_BODY, QC._RE_REQUIRED_MARKET) == []
    assert QC._missing_rows(FULL_BODY, QC._RE_REQUIRED_SENSITIVITY) == []


def test_dropped_market_section_is_detected() -> None:
    """Form A/C: the 6-4 tables never reached the markdown."""
    missing = QC._missing_rows(SENSITIVITY_BODY, QC._RE_REQUIRED_MARKET)
    assert "금리위험액(6-4)" in missing
    assert len(missing) == len(QC._RE_REQUIRED_MARKET)


def test_partial_market_section_is_detected() -> None:
    """Form B: item36 landed but 37-40 did not — the half-table case."""
    body = "6-4. 시장위험 관리\n금리위험액 1,234\n" + SENSITIVITY_BODY
    missing = QC._missing_rows(body, QC._RE_REQUIRED_MARKET)
    assert "금리위험액(6-4)" not in missing
    assert "주식위험액(6-4)" in missing


def test_dropped_sensitivity_section_is_detected() -> None:
    assert QC._missing_rows(MARKET_BODY, QC._RE_REQUIRED_SENSITIVITY) != []


def test_markers_tolerate_whitespace_between_syllables() -> None:
    """Docling splits Korean labels across cells; the patterns must not care."""
    body = "금리 위험 액\n주식  위험액\n부동산위험 액\n외환 위험액\n자산 집중 위험 액\n"
    assert QC._missing_rows(body, QC._RE_REQUIRED_MARKET) == []


# -------------------------------------------------------------------- cadence
def test_even_quarter_is_checked() -> None:
    assert QC._is_even_quarter(_meta("Q2")) is True
    assert QC._is_even_quarter(_meta("Q4")) is True


def test_odd_quarter_is_exempt() -> None:
    """1Q/3Q are 간이공시 — the sections are legitimately absent (cadence,
    not a parser gap). Flagging them would drown the review queue."""
    assert QC._is_even_quarter(_meta("Q1")) is False
    assert QC._is_even_quarter(_meta("Q3")) is False


# ---------------------------------------------------------------- ratio net
def test_page_range_span_counts_multiple_ranges() -> None:
    assert QC._page_range_span("6-38;44-47") == 33 + 4


def test_page_range_span_never_raises_on_garbage() -> None:
    for bad in ("", "abc", "4-", "-9", "4-40;", None or ""):
        assert QC._page_range_span(bad) >= 0


def test_ratio_floor_is_a_low_net_not_a_primary_signal() -> None:
    """Calibrated on 39 companies (probe_20260901b_ratio_calibration.py):
    filings missing a section (median 57.6%) and healthy ones (median 51.6%)
    overlap badly, and the OCR full-page-scan companies score *highest* while
    still being incomplete. So the floor must stay a catastrophic-failure net —
    if someone raises it into the overlap band this test fails first."""
    assert QC.REVIEW_RATIO_FLOOR < 0.30


def test_page_coverage_ratio_is_none_when_meta_incomplete() -> None:
    """The ratio needs the real PDF (it counts pages off disk), so incomplete
    front matter must yield None rather than a fabricated number."""
    assert QC._page_coverage_ratio({"quarter": "Q2"}) is None
    assert QC._page_coverage_ratio(_meta()) is None        # no source_pdf
    assert QC._page_coverage_ratio(_meta(spr="")) is None   # no selection
