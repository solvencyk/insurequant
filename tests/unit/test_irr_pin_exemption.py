# -*- coding: utf-8 -*-
"""36_irr documented exception (IRR_DERIVE_ISSUER_INCONSISTENT) 변이시험.

owner 승인 면제 6건: 2026-08-21 5건(KR0073 2025.2Q · KR0094 2024.2Q·2024.4Q·2025.2Q·2025.4Q)
+ 2026-09-01 1건(KR0094 2026.2Q — 잔차/item36 +27.97% 로 기존 대역 +5.25~25.62% 밖이지만
item36 이 시장위험 축에서 rel −0.00099% 로 닫히고 41-46 이 raw p28 과 정확 일치).
면제는 **통째 skip 이 아니라 잔차 박제**다 — 이 테스트가 그 계약을 기계로 잡아둔다.

왜 골든이 아니라 변이시험인가: 골든은 '지금 무엇이 나오는지'를 박제하므로, 면제가 조용히
blanket skip 으로 퇴화해도 그 상태 그대로 고정해 버린다. 면제의 유일한 정당성은 "잔차가
움직이면 다시 RED" 인데, 그건 값을 흔들어 봐야만 증명된다.

pre-push 훅이 `tests/unit/` 을 통째로 돌리므로 이 시험은 매 push 강제된다
(CLAUDE.md "게이트에 배선했다 ≠ 실제로 강제된다").
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

MASTER = ROOT / "kics_disclosure.json"

from solvency.validation import kics_json_rules as K            # noqa: E402
from solvency.validation.kics_json_rules import run_validation   # noqa: E402
import validate_kics_disclosure as gate                          # noqa: E402

PINNED = {("KR0073", "2025.2Q"), ("KR0094", "2024.2Q"), ("KR0094", "2024.4Q"),
          ("KR0094", "2025.2Q"), ("KR0094", "2025.4Q"), ("KR0094", "2026.2Q")}
IRR_INPUTS = (36, 41, 42, 43, 44, 45, 46)


@pytest.fixture(scope="module")
def rows():
    if not MASTER.exists():
        pytest.skip(f"master 없음: {MASTER}")
    return json.loads(MASTER.read_text(encoding="utf-8"))


def _irr_red(records) -> set:
    """룰엔진 36_irr(적용전) RED 인 (회사,분기)."""
    r = run_validation(records)
    findings = r["findings"] if isinstance(r, dict) else r
    return {(f.get("원보험사코드"), f.get("공시분기")) for f in findings
            if str(f.get("rule")) == "36_irr" and f.get("status") == "RED"}


def _irr_after_red(records) -> set:
    """게이트 적용후 축(TRANSITION_AFTER_IRR_MISMATCH) RED 인 (회사,분기)."""
    fails, _skipped = gate._transition_irr_after(records)
    return {(c, q) for c, q, *_ in fails}


def _irr_values(records, cq) -> dict:
    """그 (회사,분기)의 적용전 36·41-46 값."""
    out = {}
    for r in records:
        if (r.get("원보험사코드"), r.get("공시분기")) != cq:
            continue
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        if it in IRR_INPUTS:
            out[it] = float(str(r.get("값")).replace(",", ""))
    return out


def _mutate_cell(records, cq, item, factor=None):
    """한 (회사,분기)의 한 항목만 흔든 사본. factor=None 이면 결측 처리."""
    out = copy.deepcopy(records)
    n = 0
    for r in out:
        if (r.get("원보험사코드"), r.get("공시분기")) != cq:
            continue
        if str(r.get("항목번호")) != str(item):
            continue
        for col in ("값", "값_적용후"):
            if r.get(col) in (None, ""):
                continue
            r[col] = None if factor is None else str(
                float(str(r[col]).replace(",", "")) * factor)
            n += 1
    return out, n


# --------------------------------------------------------------------------- 범위
def test_registry_is_exactly_the_six_owner_approved_pairs():
    """면제를 이 6건 밖으로 넓히지 않는다 (owner 2026-08-21 · 2026-09-01). 두 컬럼 모두 박제돼야 한다."""
    assert set(K.IRR_DERIVE_ISSUER_INCONSISTENT) == PINNED
    for cq, pins in K.IRR_DERIVE_ISSUER_INCONSISTENT.items():
        assert set(pins) == {"적용전", "적용후"}, (
            f"{cq}: 적용전·적용후 둘 다 박제해야 한다 — 한쪽만 면제하면 다른 축이 그대로 막는다")


def test_tolerance_not_loosened():
    """허용오차로 무마하지 않았다. 박제 tol 은 마스터 소수 2자리 기준의 결정론적 값."""
    assert K.IRR_PIN_TOL == 0.01


def test_exemption_covers_no_more_than_the_current_failures(rows):
    """면제 범위 == 면제를 껐을 때 실제로 터지는 범위. 남는 게 있으면 과잉 등재다."""
    saved = K.IRR_DERIVE_ISSUER_INCONSISTENT
    K.IRR_DERIVE_ISSUER_INCONSISTENT = {}
    try:
        pre, post = _irr_red(rows), _irr_after_red(rows)
    finally:
        K.IRR_DERIVE_ISSUER_INCONSISTENT = saved
    assert pre == PINNED, f"적용전 36_irr RED 범위가 면제 범위와 다르다: {pre ^ PINNED}"
    assert post == PINNED, f"적용후 IRR RED 범위가 면제 범위와 다르다: {post ^ PINNED}"


# --------------------------------------------------------------------------- 현재 상태
def test_pins_match_live_master(rows):
    """박제잔차가 라이브 마스터에서 두 컬럼 모두 재현된다 = 면제가 살아 있다."""
    detail, _review = gate._irr_pin_recheck(rows)
    assert len(detail) == 2 * len(PINNED)
    bad = [d for d in detail if d[-1] != "MATCH"]
    assert not bad, f"박제 이탈: {bad}"


def test_exemption_on_means_no_irr_red(rows):
    assert _irr_red(rows) == set()
    assert _irr_after_red(rows) == set()


def test_disabling_exemption_restores_the_reds(rows):
    """면제를 끄면 적용전 6건 + 적용후 6건이 되살아난다."""
    saved = K.IRR_DERIVE_ISSUER_INCONSISTENT
    K.IRR_DERIVE_ISSUER_INCONSISTENT = {}
    try:
        assert _irr_red(rows) == PINNED
        assert _irr_after_red(rows) == PINNED
    finally:
        K.IRR_DERIVE_ISSUER_INCONSISTENT = saved


# --------------------------------------------------------------------------- 변이
def test_missing_input_is_red_not_skip(rows):
    """item36·41-46 중 **어느 한 칸이라도** 결측이 되면 두 축 모두 RED. 결측=SKIP 은 검증무력화다."""
    for cq in sorted(PINNED):
        for item in IRR_INPUTS:
            mut, n = _mutate_cell(rows, cq, item, factor=None)
            assert n, f"{cq} item{item}: 흔들 셀이 없다(마스터 구조 변경?)"
            assert cq in _irr_red(mut), f"{cq} item{item} 결측인데 적용전이 조용하다"
            assert cq in _irr_after_red(mut), f"{cq} item{item} 결측인데 적용후가 조용하다"


def test_perturbing_a_live_input_breaks_the_pin(rows):
    """값을 흔들면 면제가 있어도 RED.

    단 `max(R,0)` 로 절단되는 시나리오(각 쌍의 열위 시나리오)는 도출값이 **구조적으로**
    그 입력에 무감각하다 — 면제를 꺼도 룰이 못 보는 칸이라 면제가 만든 사각이 아니다.
    그래서 '도출값이 실제로 움직이는 입력'에 대해서만 RED 를 요구하고, 무감각한 입력은
    면제 ON/OFF 가 동일하게 조용하다는 것(= 면제 탓이 아님)을 함께 확인한다.
    결측 경로(위 테스트)가 그 칸들까지 전부 덮는다."""
    live_inputs = 0
    for cq in sorted(PINNED):
        vals = _irr_values(rows, cq)
        base_expected = K.irr_derive_expected(vals)
        for item in IRR_INPUTS:
            mut, n = _mutate_cell(rows, cq, item, factor=1.02)
            assert n
            # 민감도 판정은 룰 결과가 아니라 **도출식 자체**로 한다. 박제 셀은 면제를 꺼도
            # 어차피 RED 라 "면제 OFF 에서 RED 인가" 는 민감도의 대리지표가 못 된다.
            probe = dict(vals)
            probe[item] = vals[item] * 1.02
            sensitive = (item == 36) or (
                abs(K.irr_derive_expected(probe) - base_expected) > 1e-9)
            if not sensitive:
                # max(R,0) 로 절단되는 입력 — 면제 유무와 무관하게 도출값이 안 움직인다.
                assert gate._irr_pin_recheck(mut)[0], "recheck 가 비었다"
                continue
            live_inputs += 1
            assert cq in _irr_red(mut), (
                f"{cq} item{item} 을 흔들었는데 면제가 적용전 RED 를 삼켰다")
            assert cq in _irr_after_red(mut), (
                f"{cq} item{item} 을 흔들었는데 면제가 적용후 RED 를 삼켰다")
    assert live_inputs >= 6 * 5, f"민감 입력이 너무 적다({live_inputs}) — 시험이 무력해졌다"


def test_pin_registry_is_provenance_checked():
    """레지스트리가 근거 원장 검사를 받는다. 등록을 빠뜨리면 근거 없이 조용히 사는 면제가 된다."""
    regs = gate._exemption_registries()
    assert "IRR_DERIVE_ISSUER_INCONSISTENT" in regs
    assert regs["IRR_DERIVE_ISSUER_INCONSISTENT"] == frozenset(PINNED)
    red, _review = gate._exemption_provenance_findings()
    mine = [r for r in red if r.get("registry") == "IRR_DERIVE_ISSUER_INCONSISTENT"]
    assert not mine, f"근거 원장 RED: {mine}"
