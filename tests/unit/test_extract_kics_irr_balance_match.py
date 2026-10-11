# -*- coding: utf-8 -*-
"""scripts/extract_kics_irr_balance.py 의 컬럼->시나리오 사상: 위치 대응 우선(2026-10-11).

K-ICS 금리위험액 현황 표의 열 순서는 고정이다(충격 전 | 평균회귀 | 금리상승 | 금리하락 | 금리평탄 | 금리경사 = 항목 41..46).
종전의 「순자산가치 값 근접(허용 0.55억원·3e-4) + 첫 미사용 열」 대응은 시나리오 값이 허용치 안에 모이는 표에서 열이 뒤바뀌었다
(하나손보 2025.2Q: 평균회귀 5011.25 대 금리하락 5009.95 = 차 1.30 ≤ 허용 1.50 → 항목 42·44 가 서로 바뀜, 카카오페이손보 5개 분기: 모든 시나리오가 0.55억원 안).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import extract_kics_irr_balance as I  # noqa: E402

# 하나손해보험 FY2025_Q2 p34-35 의 순자산가치 6열(백만원)과 마스터 항목 41..46(억원)
HANA_NAV = [498871, 501125, 488784, 500995, 475694, 520845]
HANA_M = {41: 4988.71, 42: 5011.25, 43: 4887.84, 44: 5009.95, 45: 4756.94, 46: 5208.45}


def old_value_matching(nav, m, tol_rel=3e-4):
    """HEAD 의 값 근접 대응(재현용 사본)."""
    for scale in I._SCALES:
        pos, used, ok = {}, set(), True
        for it in (41, 43, 44):
            mv = m.get(it)
            tol = max(0.55, abs(mv) * tol_rel)
            c = [p for p, v in enumerate(nav) if p not in used and abs(v * scale - mv) <= tol]
            if not c:
                ok = False
                break
            pos[it] = c[0]
            used.add(c[0])
        if not ok:
            continue
        for it in (42, 45, 46):
            mv = m.get(it)
            tol = max(0.55, abs(mv) * tol_rel)
            c = [p for p, v in enumerate(nav) if p not in used and abs(v * scale - mv) <= tol]
            if c:
                pos[it] = c[0]
                used.add(c[0])
        return pos, scale
    return None


def test_old_value_matching_swapped_the_hana_columns_and_positional_does_not():
    old = old_value_matching(HANA_NAV, HANA_M)
    assert old is not None and old[0][42] == 3 and old[0][44] == 1          # 버그: 평균회귀 ↔ 금리하락
    pos, scale = I.match(HANA_NAV, HANA_M)
    assert scale == 0.01
    assert pos == {41: 0, 43: 2, 44: 3, 42: 1, 45: 4, 46: 5}


def test_flat_table_all_scenarios_within_tolerance_maps_by_position():
    nav = [-79959, -80002, -79913, -80006, -79940, -79978]                  # 카카오페이손보 2023.2Q (천원)
    m = {41: -0.8, 42: -0.8, 43: -0.8, 44: -0.8, 45: -0.8, 46: -0.8}        # 마스터는 2자리 반올림이라 전부 같다
    pos, scale = I.match(nav, m)
    assert scale == 1e-5 and {it: pos[it] for it in (41, 42, 43, 44, 45, 46)} == {41: 0, 42: 1, 43: 2, 44: 3, 45: 4, 46: 5}


def test_falls_back_to_value_matching_when_the_table_order_is_not_the_standard_one():
    m = {41: 1000.0, 42: 1100.0, 43: 900.0, 44: 1200.0, 45: 1050.0, 46: 950.0}
    nav = [1000, 900, 1100, 1200, 950, 1050]                                # 열 순서가 다른 표: 위치 앵커가 안 맞는다
    assert I.match_positional(nav, m) is None
    pos, scale = I.match(nav, m)
    assert scale == 1.0 and pos == {41: 0, 43: 1, 44: 3, 42: 2, 45: 5, 46: 4}


def test_positional_needs_six_columns_and_all_three_anchors():
    assert I.match_positional([1, 2, 3], {41: 1.0, 43: 3.0, 44: 4.0}) is None
    assert I.match_positional([100, 110, 90, 120, 105, 95], {41: 100.0, 43: None, 44: 120.0}) is None
