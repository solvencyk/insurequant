# -*- coding: utf-8 -*-
"""Golden unit test for the IFRS17 CSM extractor scoring (REFACTOR-1, 2026-06-13).

Locks the no-regression contract for moving scoring KEYWORDS to
data/ifrs17/table_scoring_keywords.yaml + the shared scoring.py loader:

1. The loaded keyword config is BYTE-IDENTICAL to the extractor's prior
   hardcoded constants (so the YAML externalisation changed no behaviour).
2. score_table() classifies the canonical CSM-amortisation table shapes
   exactly as before (caption gate, year-bucket form types, non-CSM cap).

Ported from the K-ICS pattern (tests/unit/test_kics_disclosure_parser.py).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ifrs17 import csm_extractor as C  # noqa: E402
from ifrs17.scoring import load_scoring  # noqa: E402


# --- 1. config byte-identical to the prior hardcoded constants ---------------

def test_csm_keywords_match_legacy_constants():
    """If these drift, the YAML diverged from the code's historical behaviour."""
    sc = load_scoring("csm")
    assert sc.caption_primary == ("보험계약마진",)
    assert sc.caption_verbs == ("상각", "예상", "인식", "향후", "인식시기", "기대상각")
    assert sc.negative_topic_words == ("부채변동", "공정가치", "위험조정", "할인율", "현금흐름")
    assert sc.total_words == ("계", "합계", "총계", "합 계", "총 계")


def test_csm_module_constants_sourced_from_config():
    assert C._CAPTION_PRIMARY == "보험계약마진"
    assert C._CAPTION_VERBS == ("상각", "예상", "인식", "향후", "인식시기", "기대상각")
    assert C._NEGATIVE_TOPIC_WORDS == ("부채변동", "공정가치", "위험조정", "할인율", "현금흐름")
    assert C._TOTAL_WORDS == ("계", "합계", "총계", "합 계", "총 계")


def test_unknown_extractor_yields_empty_config():
    sc = load_scoring("does_not_exist")
    assert sc.caption_primary == () and sc.total_words == ()


# --- 2. score_table classification (canonical shapes) ------------------------

def _table(caption, header, rows):
    return C.ExtractedTable(caption=caption, header=[header], rows=rows,
                            footnotes=[], line_no=1)


def test_score_table_csm_amort_with_year_buckets_form_A():
    """CSM caption + 3 year-bucket columns + 합계 → high score, form_type A."""
    t = _table(
        "② 보험계약마진 상각",
        ["구분", "1년", "1년~2년", "2년~3년", "합계"],
        [["포트폴리오A", "10", "20", "30", "60"]],
    )
    st = C.score_table(t)
    assert st.score >= 4, (st.score, st.reasons)
    assert st.form_type == "A", st.form_type


def test_score_table_year_buckets_on_rows_form_A_rows():
    """Year buckets on the LEFT column (DB손해 style) → form_type A_rows."""
    t = _table(
        "보험계약마진 상각 예상",
        ["구분", "원수", "합계"],
        [["1년", "10", "10"], ["1년~2년", "20", "20"], ["2년~3년", "30", "30"]],
    )
    st = C.score_table(t)
    assert st.form_type == "A_rows", st.form_type
    assert st.score >= 4, (st.score, st.reasons)


def test_score_table_non_csm_topic_capped():
    """Structural-only signals without a CSM caption are capped at <=3."""
    t = _table(
        "보험부채 공정가치 변동",
        ["구분", "1년", "1년~2년", "2년~3년", "합계"],
        [["x", "1", "2", "3", "6"]],
    )
    st = C.score_table(t)
    assert st.score <= 3, (st.score, st.reasons)


# --- 3. end-to-end: pick the right table out of a real multi-table filing ----
# (GOLDEN-E2E, owner review 2026-06-13). The score_table tests above feed
# synthetic single tables; this drives the full extract_csm_tables() over a
# hermetic fixture of REAL 메리츠 KR0001 2025.4Q values containing two decoys
# (a balance sheet and a 위험조정 변동 note) plus the genuine CSM table, proving
# the extractor SELECTS the right one — the gap a unit test on one table misses.

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "csm_e2e_meritz_2025q4.xml"


def test_e2e_selects_csm_table_from_multitable_filing():
    tabs = C.extract_csm_tables(_FIXTURE)
    assert tabs, "no CSM table scored >= 4"
    top = tabs[0]
    # right table chosen: CSM 향후 상각 caption, not a decoy
    assert "보험계약마진" in top.caption and ("상각" in top.caption or "향후" in top.caption)
    assert top.score >= 4, (top.score, top.reasons)
    # the two decoys must never be selected
    assert all(
        "재무상태표" not in t.caption and "위험조정 변동" not in t.caption for t in tabs
    )
    # real residual-maturity total for 발행한 보험계약 (<당기말>)
    issued = next(r for r in top.rows if r and r[0].startswith("발행한 보험계약"))
    assert issued[-1] == "11,103,697"
