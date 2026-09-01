"""Pins the page-selection guard added for inbox 20260831T0700Z.

Three distinct docling failure forms were measured on the 2026.2Q round:

  A  the required section's page was never selected (top-N cap evicted it)
  B  the section's table reached the MD only in part
  C  the page WAS selected, docling raised ``std::bad_alloc`` in its preprocess
     stage, returned ``PARTIAL_SUCCESS``, and the page's content silently
     vanished from the markdown

Before this guard nothing read ``source_page_ranges`` / ``keyword_hit_pages``,
so all three read downstream as "the filer did not disclose it". These tests
keep the detection wired; deleting a check breaks a test rather than a quarter.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solvency.parser import docling_parser as DP
from solvency.parser import quality_check as QC

EVEN_Q_META = {
    "period": "FY2026_Q2",
    "quarter": "Q2",
    "parse_scope": "keyword_window",
    "source_page_ranges": "4-40",
    "source_total_pages": "60",
}

FULL_BODY = "6-4. 시장위험 관리\n금리위험액 현황\n6-8. 위험민감도\n금리 민감도 분석\n"


def test_even_quarter_full_body_is_clean() -> None:
    assert QC.page_selection_flags(dict(EVEN_Q_META), FULL_BODY) == []


def test_missing_market_section_flags_even_quarter() -> None:
    flags = QC.page_selection_flags(dict(EVEN_Q_META), "6-8. 위험민감도\n금리 민감도\n")
    assert any(f.startswith("SECTION_MISSING=6-4") for f in flags), flags


def test_missing_sensitivity_section_flags_even_quarter() -> None:
    flags = QC.page_selection_flags(dict(EVEN_Q_META), "6-4. 시장위험 관리\n금리위험액 현황\n")
    assert any(f.startswith("SECTION_MISSING=6-8") for f in flags), flags


def test_odd_quarter_is_exempt() -> None:
    """Q1/Q3 are 간이공시 — the detail sections are legitimately absent."""

    meta = dict(EVEN_Q_META, period="FY2026_Q1", quarter="Q1")
    assert QC.page_selection_flags(meta, "본문에 아무 절도 없다") == []


def test_sensitivity_not_required_before_2024q4() -> None:
    """6-8 위험민감도 did not exist in the earlier template (0/37 in 2023.2Q)."""

    meta = dict(EVEN_Q_META, period="FY2023_Q2", quarter="Q2")
    flags = QC.page_selection_flags(meta, "6-4. 시장위험 관리\n금리위험액 현황\n")
    assert not [f for f in flags if "6-8" in f], flags


def test_unrecovered_docling_pages_flag() -> None:
    meta = dict(
        EVEN_Q_META,
        docling_status="PARTIAL_SUCCESS",
        docling_dropped_pages="29,30",
        docling_unrecovered_pages="30",
    )
    flags = QC.page_selection_flags(meta, FULL_BODY)
    assert "DOCLING_PAGES_LOST=30" in flags, flags


def test_recovered_docling_pages_do_not_flag() -> None:
    meta = dict(
        EVEN_Q_META,
        docling_status="RECOVERED",
        docling_dropped_pages="29,30",
        docling_recovered_pages="29,30",
        docling_unrecovered_pages="",
    )
    assert QC.page_selection_flags(meta, FULL_BODY) == []


def test_thin_selection_flags_even_quarter_only() -> None:
    thin = dict(EVEN_Q_META, source_page_ranges="4-8")
    assert any(f.startswith("PAGE_SELECTION_THIN") for f in QC.page_selection_flags(thin, FULL_BODY))
    odd = dict(thin, period="FY2026_Q1", quarter="Q1")
    assert not [f for f in QC.page_selection_flags(odd, FULL_BODY) if f.startswith("PAGE_SELECTION_THIN")]


def test_priority_page_survives_the_top_n_cap(monkeypatch) -> None:
    """A 시장위험 page scoring 1 must not be evicted by 20 higher-scoring pages.

    Measured on the real 2026.2Q filings, 8 such pages ranked 21-36 out of
    22-62 candidates and fell outside the cap (KR0002 p33, KR0032 p32,
    KR0049 p35/36, KR0050 p34, KR0074 p25, KR0083 p30, KR0150 p28).
    """

    # 20 fat non-priority pages + one lean priority page at the very end.
    hits = [(p, 8, False) for p in range(1, 21)] + [(50, 1, True)]
    monkeypatch.setattr(DP, "_find_keyword_pages", lambda path, terms: (hits, 60))
    item = DP.PdfInput(
        company_code="KR9999",
        company_dirname="KR9999_test",
        period="FY2026_Q2",
        pdf_path=Path("never-opened.pdf"),
        keyword_window=0,
    )
    ranges, mode, top_pages = DP._select_page_ranges(item)
    assert 50 in top_pages, top_pages
    assert mode == "keyword_window_priority"
    assert any(lo <= 50 <= hi for lo, hi in ranges), ranges


def test_non_priority_page_is_still_capped(monkeypatch) -> None:
    hits = [(p, 8, False) for p in range(1, 21)] + [(50, 1, False)]
    monkeypatch.setattr(DP, "_find_keyword_pages", lambda path, terms: (hits, 60))
    item = DP.PdfInput(
        company_code="KR9999",
        company_dirname="KR9999_test",
        period="FY2026_Q2",
        pdf_path=Path("never-opened.pdf"),
        keyword_window=0,
    )
    _, mode, top_pages = DP._select_page_ranges(item)
    assert 50 not in top_pages
    assert mode == "keyword_window"


class _FakeProv:
    def __init__(self, page_no: int) -> None:
        self.page_no = page_no


class _FakeItem:
    def __init__(self, page_no: int) -> None:
        self.prov = [_FakeProv(page_no)]
        self.text = "x"


class _FakeDoc:
    """Mimics the shape docling returns after a preprocess-stage bad_alloc:
    the page index still lists every page, but the failed pages own no items."""

    def __init__(self, pages: list[int], with_content: list[int]) -> None:
        self.pages = {p: object() for p in pages}
        self.texts = [_FakeItem(p) for p in with_content]
        self.tables = []
        self.pictures = []


def test_pages_missing_content_finds_the_silent_drop() -> None:
    doc = _FakeDoc(pages=list(range(5, 36)), with_content=[p for p in range(5, 36) if p not in (29, 30, 33, 34)])
    assert DP._pages_missing_content(doc) == [29, 30, 33, 34]


def test_pages_missing_content_clean_document() -> None:
    doc = _FakeDoc(pages=[1, 2, 3], with_content=[1, 2, 3])
    assert DP._pages_missing_content(doc) == []
