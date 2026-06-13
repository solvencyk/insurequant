# -*- coding: utf-8 -*-
"""Golden unit test for the IFRS17 bs_snapshot extractor scoring (REFACTOR-2).

Locks the no-regression contract for sourcing bs_snapshot's scoring KEYWORDS
(caption / header / row-stub / slice / rollforward sets) from
data/ifrs17/table_scoring_keywords.yaml via the shared scoring.py loader: the
loaded config must be BYTE-IDENTICAL to the extractor's prior constants, and
_score_table() must still rank a BS snapshot table positively.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ifrs17 import bs_snapshot_extractor as B  # noqa: E402
from ifrs17.scoring import load_scoring  # noqa: E402


def test_bs_snapshot_keywords_match_legacy_constants():
    assert B._CAPTION_KEYWORDS == (
        "보험계약부채", "자산부채", "현황", "(1)",
        "보험계약자산및부채", "보험계약자산부채", "재보험계약자산및부채",
        "보험계약부채(자산)", "보험계약자산(부채)", "재보험계약자산(부채)",
        "발행한 보험계약", "세부내역", "보고기간종료일", "금액은 다음", "당기말과 전기말",
    )
    assert B._HEADER_BS == (
        "보험계약부채", "순보험계약부채", "보험계약자산",
        "재보험계약자산", "재보험계약부채", "순재보험계약자산",
    )
    assert B._HEADER_BS_TRIPLE == ("자산", "부채", "합계", "합 계")
    assert B._HEADER_BS_SLICES == ("장기", "일반", "자동차", "생명")
    assert B._ROW_STUBS == (
        "보험계약부채", "순보험계약부채", "보험계약자산",
        "재보험계약자산", "재보험계약부채", "순재보험계약자산",
    )
    assert B._ROW_SLICES == ("장기", "일반", "자동차", "생명")
    assert B._ROLLFORWARD_MARKERS == ("변동내역", "측정요소", "잔여보장", "발생사고")


def test_bs_snapshot_extra_keys_present():
    """All bespoke keyword sets ride in ScoringConfig.extra."""
    sc = load_scoring("bs_snapshot")
    assert set(sc.extra) >= {
        "caption_keywords", "header_bs", "header_bs_triple", "header_bs_slices",
        "row_stubs", "row_slices", "rollforward_markers",
    }


def test_score_table_bs_snapshot_scores_positive():
    """A 보험계약자산및부채 현황 table with BS header line items + matching row
    stubs should score well above zero."""
    t = B.ExtractedBsSnapshotTable(
        caption="(1) 보험계약자산및부채 현황 세부내역",
        header=[["구분", "보험계약부채", "보험계약자산", "순보험계약부채"]],
        rows=[
            ["보험계약부채", "1000", "0", "1000"],
            ["보험계약자산", "0", "50", "-50"],
            ["순보험계약부채", "1000", "50", "950"],
        ],
        footnotes=[],
        line_no=1,
    )
    score, block_type, *_ = B._score_table(t, "삼성화재")
    assert score >= 5, (score, block_type)
