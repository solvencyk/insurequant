# -*- coding: utf-8 -*-
"""Golden no-regression test for insurance_pl + reinsurance extractor scoring
(REFACTOR-2, 2026-06-13). Locks that sourcing their scoring KEYWORDS from
data/ifrs17/table_scoring_keywords.yaml via scoring.py left the constants
BYTE-IDENTICAL to the pre-refactor hardcoded values (incl. historical OCR-typo
spellings 위허조정/위허해제 and the 재보험자 불이행위허 stub, kept on purpose)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ifrs17 import insurance_pl_extractor as P  # noqa: E402
from ifrs17 import reinsurance_extractor as R  # noqa: E402


def test_insurance_pl_keywords_byte_identical():
    assert P._CAPTION_PRIMARY == ("보험손익", "보험수익", "보험서비스", "서비스결과", "상세내역")
    assert P._CAPTION_SECONDARY == ("상세", "(5)", "원수", "보험손익")
    assert P._ROW_STUBS_STRONG == (
        "보험수익", "보험서비스비용", "총 보험서비스결과", "보험서비스결과",
        "당기손익으로 인식한 보험계약마진", "예상보험금 및 보험서비스비용",
        "위허해제에 따른 위허조정 변동", "보험서비스수익", "총 보험수익",
        "총 보험비용", "보험서비스수익 합계", "보험서비스비용 합계",
    )
    assert P._ROW_STUBS_WEAK == (
        "보험송취현금흐름", "손실부담계약", "보험금 및 보험서비스비용",
        "일반보험서비스수익", "일반보험서비스비용", "보험비용",
    )
    assert P._RI_BLOCK_MARKERS == ("출재", "재보험", "순재보험", "출재보험")


def test_reinsurance_keywords_byte_identical():
    assert R._CAPTION_PRIMARY == ("출재", "재보험", "순재보험", "출재보험")
    assert R._CAPTION_SECONDARY == ("변동내역", "측정요소", "상세변동", "(3)", "(4)")
    assert R._ROW_STUBS_STRONG == (
        "기초 재보험계약자산", "기초 재보험계약부채", "기말 재보험계약자산",
        "재보험료의 배분", "재보험 순원가", "순재보험금융손익",
        "재보험자 불이행위허", "당기손익으로 인식한 보험계약마진",
    )
    assert R._ROW_STUBS_WEAK == ("기초", "기말", "경험조정", "위허해제")


def test_both_share_measurement_header_and_block_markers():
    # header + block markers are the copy-pasted sets now sourced from one YAML.
    assert P._HEADER_MEASUREMENT == R._HEADER_MEASUREMENT
    assert P._DIRECT_BLOCK_MARKERS == R._DIRECT_BLOCK_MARKERS == ("원수", "수재(원수", "순보험계약부채", "보험계약부채", "보험계약자산")


# --- end-to-end: pick the right table out of a real multi-table filing -------
# (GOLDEN-E2E expansion, owner parser_refactor; mirrors the csm E2E fixture).
# The byte-identical-constant tests above don't prove SELECTION; these drive the
# full extract_*_tables() over hermetic fixtures of REAL 삼성화재 (rcept
# 20250311001055) FY2024 values, each containing a 재무상태표 decoy plus the
# wrong-block sibling (a ceded 재보험비용 for insurance_pl; a direct 보험손익 for
# reinsurance), proving each extractor SELECTS its right table and rejects the
# decoys — the gap a synthetic single-table unit test misses.

_FIX_DIR = Path(__file__).resolve().parent / "fixtures"


def test_e2e_selects_insurance_pl_table_from_multitable_filing():
    tabs = P.extract_insurance_pl_tables(
        _FIX_DIR / "insurance_pl_e2e_samsungfire_2024.xml", company_name="삼성화재해상보험"
    )
    assert tabs, "no insurance P&L table scored >= 5"
    top = tabs[0]
    # right table chosen: direct 보험손익 detail, not the ceded 재보험비용 decoy
    assert "보험손익" in top.caption
    assert top.block_type in ("direct", "mixed"), top.block_type
    assert top.score >= 5, (top.score, top.reasons)
    assert top.mvp_candidate, top.reasons
    # the two decoys must never be selected
    assert all(
        "재무상태표" not in t.caption and "재보험비용" not in t.caption for t in tabs
    )
    # real direct P&L rows: CSM 상각 (장기 only) and the 합계 across 장기/자동차/일반
    csm = next(r for r in top.rows if r and r[0] == "보험계약마진 상각")
    assert csm == ["보험계약마진 상각", "1,612,298", "-", "-", "1,612,298"], csm
    total = next(r for r in top.rows if r and r[0] == "합계")
    assert total == ["합계", "8,833,157", "5,619,497", "2,823,810", "17,276,464"], total


def test_e2e_selects_reinsurance_table_from_multitable_filing():
    tabs = R.extract_reinsurance_tables(
        _FIX_DIR / "reinsurance_e2e_samsungfire_2024.xml", company_name="삼성화재해상보험"
    )
    assert tabs, "no reinsurance table scored >= 5"
    top = tabs[0]
    # right table chosen: ceded 출재 신용위험 익스포져, not the direct 보험손익 decoy
    assert "출재보험계약" in top.caption and "신용위험 익스포져" in top.caption
    assert top.block_type == "reinsurance", top.block_type
    assert top.score >= 5, (top.score, top.reasons)
    assert top.mvp_candidate, top.reasons
    # the two decoys must never be selected
    assert all(
        "재무상태표" not in t.caption and "보험손익" not in t.caption for t in tabs
    )
    # real ceded credit-exposure rows: 장기보험 [당기,전기] and the 합계
    jang = next(r for r in top.rows if r and r[0].startswith("장기보험"))
    assert jang == ["장기보험(*)", "232,578", "379,793"], jang
    total = next(r for r in top.rows if r and r[0] == "합계")
    assert total == ["합계", "1,382,954", "1,416,757"], total
