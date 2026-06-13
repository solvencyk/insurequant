# -*- coding: utf-8 -*-
"""Golden unit test for the IFRS17 sensitivity extractor scoring (REFACTOR-2).

Locks the no-regression contract for sourcing sensitivity's scoring KEYWORDS
(assumption / sensitivity caption + row sets, rollforward sets, negative-topic
words) from data/ifrs17/table_scoring_keywords.yaml via the shared scoring.py
loader: the loaded config must be BYTE-IDENTICAL to the extractor's prior
constants, and _score_table() must still rank a sensitivity table positively.

NOTE: several values carry historical OCR-typo spellings (보험위허/위허률/
잔여보작/비금융위허) that MATCH the docling MD text — locked byte-identical here.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ifrs17 import sensitivity_extractor as S  # noqa: E402
from ifrs17.scoring import load_scoring  # noqa: E402


def test_sensitivity_keywords_match_legacy_constants():
    assert S._CAPTION_ASSUMPTION == ("현행 추정 가정", "계리적 가정", "가정값", "(2)")
    assert S._CAPTION_SENSITIVITY == ("가정민감도", "민감도 분석", "민감도분석", "보험위허")
    assert S._NEGATIVE == ("금융상품", "수준3", "공정가치")
    assert S._ROW_ASSUMPTION == ("위허률", "해약률", "사업비", "할인율", "신뢰수준")
    assert S._ROW_SENSITIVITY == (
        "위허률", "해약률", "사업비", "사업비율", "손해율",
        "당기손익 영향", "잔여보작", "위허률 가정 변경", "해약률 가정 변경",
    )
    assert S._CAPTION_ROLLFORWARD == (
        "측정요소", "변동 세부", "변동내역", "미래서비스 관련", "상세변동",
    )
    assert S._ROW_ROLLFORWARD == (
        "당기 최초 인식", "가정변경효과", "보험계약마진 추정의 변경",
        "물량차이", "기초 순장부금액", "기말 순장부금액",
    )
    assert S._HEADER_ROLLFORWARD == (
        "미래현금흐름의 현재가치 추정치", "비금융위허에대한 위허조정",
    )


def test_sensitivity_extra_keys_present():
    """All bespoke keyword sets ride in ScoringConfig.extra."""
    sc = load_scoring("sensitivity")
    assert set(sc.extra) >= {
        "caption_assumption", "caption_sensitivity", "negative",
        "row_assumption", "row_sensitivity", "caption_rollforward",
        "row_rollforward", "header_rollforward",
    }


def test_score_table_sensitivity_scores_positive():
    """A 민감도 분석 table with sensitivity caption + matching row stubs should
    score well above zero."""
    t = S.ExtractedSensitivityTable(
        caption="(3) 가정민감도 분석",
        header=[["구분", "당기손익", "잔여보작"]],
        rows=[
            ["위허률 가정 변경", "10", "20"],
            ["해약률 가정 변경", "-5", "-8"],
            ["사업비", "3", "4"],
        ],
        footnotes=[],
        line_no=1,
    )
    score, block_type, slice_label, slice_policy, table_kind, reasons = S._score_table(t, "삼성화재")
    assert score >= 4, (score, table_kind, reasons)
