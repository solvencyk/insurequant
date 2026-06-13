# -*- coding: utf-8 -*-
"""Golden unit test for the IFRS17 measurement extractor scoring (REFACTOR-2).

Locks the no-regression contract for sourcing measurement's scoring KEYWORDS
(caption / header / row-stub + direct/ri/short-term block markers) from
data/ifrs17/table_scoring_keywords.yaml via the shared scoring.py loader:
the loaded config must be BYTE-IDENTICAL to the extractor's prior constants,
and score_table() must still rank a measurement rollforward table positively.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ifrs17 import measurement_extractor as M  # noqa: E402
from ifrs17.scoring import load_scoring  # noqa: E402


def test_measurement_keywords_match_legacy_constants():
    assert M._CAPTION_PRIMARY == ("측정요소", "변동내역", "보험부채 상세변동", "상세변동내역", "구성요소별")
    assert M._CAPTION_SECONDARY == ("보험부채", "보험계약부채", "원수", "출재")
    assert M._HEADER_MEASUREMENT == (
        "미래 현금흐름", "현재가치 추정치", "미래현금흐름", "위허조정",
        "보험계약마진", "수정소급", "공정가치", "그 외 보험계약", "합계",
    )
    assert M._ROW_STUBS_STRONG == (
        "기초 순장부금액", "기말 순장부금액", "당기손익으로 인식한 보험계약마진",
        "신계약효과", "보험서비스결과", "순보험금융손익", "기초 보험계약 순부채",
        "기초 출재보험계약 순부채", "기말 보험계약 순부채", "보험계약마진 상각",
    )
    assert M._ROW_STUBS_WEAK == ("기초", "기말", "경험조정", "위허해제")
    # DEDUP-2: original had a duplicated last element; collapsed to one (no-op for
    # the membership check has_short_term_markers). Owner-approved 2026-06-13.
    assert M._SHORT_TERM_MARKERS == ("일반", "자동차", "보험료배분접근법을 적용하는")
    assert M._DIRECT_BLOCK_MARKERS == ("원수", "수재(원수", "순보험계약부채", "보험계약부채", "보험계약자산")
    assert M._RI_BLOCK_MARKERS == ("출재", "재보험", "순재보험", "출재보험")


def test_measurement_extra_block_markers_present():
    """The non-standard keyword sets ride in ScoringConfig.extra."""
    sc = load_scoring("measurement")
    assert set(sc.extra) >= {"short_term_markers", "direct_block_markers", "ri_block_markers"}


def test_score_table_measurement_rollforward_scores_positive():
    """A 구성요소별 변동 table with measurement columns + strong rollforward
    stubs should score well above zero (MVP candidate region)."""
    t = M.ExtractedMeasurementTable(
        caption="(1) 구성요소별 보험부채 상세변동내역 (원수)",
        header=[["구분", "미래현금흐름", "위허조정", "보험계약마진", "합계"]],
        rows=[
            ["기초 순장부금액", "100", "10", "20", "130"],
            ["보험계약마진 상각", "-", "-", "-5", "-5"],
            ["기말 순장부금액", "110", "9", "16", "135"],
        ],
        footnotes=[],
        line_no=1,
    )
    score, block_type, *_ = M._score_table(t, "삼성화재")
    assert score >= 4, (score, block_type)
    assert block_type in ("direct", "mixed", "unknown"), block_type


# --- end-to-end: pick the right table out of a real multi-table filing -------
# (GOLDEN-E2E expansion, owner parser_refactor; mirrors the csm E2E fixture).
# The score_table test above feeds a synthetic single table; this drives the
# full extract_measurement_tables() over a hermetic fixture of REAL 삼성화재
# (rcept 20250311001055) FY2024 values containing two decoys (a 재무상태표 and a
# 위험조정 변동 note) plus the genuine 장기손해보험 보험부채 변동내역 table, proving
# the extractor SELECTS the right one — the gap a unit test on one table misses.

_E2E_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "measurement_e2e_samsungfire_2024.xml"
)


def test_e2e_selects_measurement_table_from_multitable_filing():
    tabs = M.extract_measurement_tables(_E2E_FIXTURE, company_name="삼성화재해상보험")
    assert tabs, "no measurement table scored >= 5"
    top = tabs[0]
    # right table chosen: 보험부채 변동내역 measurement caption, not a decoy
    assert "보험부채 변동내역" in top.caption
    assert top.score >= 5, (top.score, top.reasons)
    assert top.mvp_candidate, top.reasons
    # the two decoys must never be selected
    assert all(
        "재무상태표" not in t.caption and "위험조정 변동내역" not in t.caption
        for t in tabs
    )
    # real 신계약 measurement row [FCF추정치, 위험조정, CSM] for 장기손해보험
    sin = next(r for r in top.rows if r and r[0] == "신계약")
    assert sin == ["신계약", "(3,725,042)", "312,676", "3,451,183"], sin
