# -*- coding: utf-8 -*-
"""`IDENTITY_TAUTOLOGY` 변이시험 (티켓 inbox/validation/20260821T1500Z §4).

## 이 테스트가 지키는 것

동어반복 탐지기는 **자기 자신이 동어반복이 되기 가장 쉬운 룰**이다. 임계를 조금만 올리면
영원히 0건이 되고, 그 0 은 "축이 깨끗하다"로 읽힌다 — 이 룰이 잡으려는 바로 그 병이다.
그래서 정적 확인(임계 상수를 읽는 것)으로는 부족하고, **되맞춘 데이터를 만들어 실제로
발화하는지**를 매번 다시 확인한다.

  1. 건전한 축(R6: item16 = Σ(17..21) − item15, 실측 excess 1.11)을 인위적으로 되맞추면
     → 발화해야 한다.
  2. 같은 축이 원래 데이터에서는 → 발화하면 안 된다.

두 방향을 다 보는 이유: ①만 보면 "무조건 발화"하는 고장난 룰이 통과하고, ②만 보면
"무조건 침묵"하는 고장난 룰이 통과한다.

## 귀무모형도 같이 고정한다

`_taut_null_p0` 가 조용히 바뀌면 excess 의 분모가 바뀌어 임계가 의미를 잃는다. 닫힌형
Irwin–Hall 값을 손으로 검산 가능한 상수와 대조해 못 박는다(k=2 → 정확히 3/4).

## ⚠️ 이 탐지기를 PL_breakdown 에 배선하지 마라 (2026-08-29 실측)

이 파일의 우주는 `kics_disclosure.json` 하나다(`_taut_axes()` 실측 5축, 전부 K-ICS 항목번호
축). PL 마스터에 같은 사각이 훨씬 크게 있다는 것이 2026-08-29 에 확인됐지만
(`PL_BRIDGE` pass 3,057 중 1,608 이 구성상 참), **이 탐지기를 그대로 옮기면 안 된다.**

`_taut_null_p0(k)` 는 각 항이 **등식 자신의 단위로 반올림**됐다고 가정한다(K-ICS 는 백만원
정수). PL 마스터 값은 원 ÷ 1e6 후 `round(6)` 이라 **원 단위 정밀도가 살아 있어서, 발행사가
제대로 공시한 건전한 항등식도 잔차가 정확히 0** 이 된다. 실측:

```
eq                            n   zeros   rate   null  excess     z   RED?  실제판정
EQ1 3=4+5+6+7               315     313  0.994  0.602    1.65  14.2   RED   TAUTOLOGY
EQ5 20=1+17                 327     320  0.979  0.750    1.30   9.5   RED   REAL   <- 오탐
EQ8 31=24+25                282     282  1.000  0.750    1.33   9.7   RED   REAL   <- 오탐
EQ9 25=26+..+32             221     219  0.991  0.513    1.93  14.2   RED   REAL   <- 오탐, 최고 excess
```

**9축 전부 RED 이고 excess 1위(1.93)가 하필 진짜 검산 축인 EQ9 다** — 통계가 두 부류를
분리하지 못한다(`_TAUT_MIN_CELLS=30` 도 문제가 아니다, n≈300). 즉 "탐지기를 PL 에 배선하는
것을 잊었다"가 아니라 **"이 탐지기는 그 마스터에서 작동하지 않는다"** 가 결론이다.
재현: `scripts/_probes/probe_20260829_taut_detector_on_pl.py`.

PL 쪽 판별자는 통계가 아니라 **write-path 추적 + CONSTRUCTIVE 변이시험**이고, 그 결과는
`validate_master_tables.PL_EQ_EVIDENCE`(등식별 REAL/TAUTOLOGY/PARTIAL 상수, SUMMARY 가 인쇄)
와 `tests/test_rule_coverage_manifest.py::PL_CONSTRUCTIVE_BLIND`(변이시험 박제)에 있다.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
MASTER = ROOT / "kics_disclosure.json"

import validate_kics_disclosure as gate  # noqa: E402

# 되맞춤 시험 대상 = 건전 대조군 중 표본이 가장 크고 잔차가 가장 풍부한 축.
MUTATE_AXIS = "R6_item16"
MUTATE_TARGET = 16
MUTATE_TERMS = {17: +1, 18: +1, 19: +1, 20: +1, 21: +1, 15: -1}


@pytest.fixture(scope="module")
def rows():
    if not MASTER.exists():
        pytest.skip(f"master 없음: {MASTER}")
    return json.loads(MASTER.read_text(encoding="utf-8"))


def _red_axes(records):
    census, drift = gate._identity_tautology_census(records)
    assert not drift, f"축 정의 불일치(TAUTOLOGY_AXIS_SPEC_DRIFT): {drift}"
    red, _review, _exempt = gate._identity_tautology_findings(census)
    return {(r["axis"], r["column"]) for r in red}, {(r["axis"], r["column"]): r for r in census}


def test_null_model_pinned():
    """반올림 귀무 P(잔차=0). k=2 는 손으로 검산되는 정확값 3/4 다."""
    assert gate._taut_null_p0(2) == pytest.approx(0.75, abs=1e-12)
    assert gate._taut_null_p0(3) == pytest.approx(2 / 3, abs=1e-12)
    # 항 수가 늘수록 반올림 잡음이 쌓여 정확0 이 드물어진다 — 이 단조성이 룰의 근거다.
    seq = [gate._taut_null_p0(k) for k in range(2, 9)]
    assert seq == sorted(seq, reverse=True), f"귀무가 단조감소하지 않는다: {seq}"


def test_thresholds_sit_inside_the_measured_gap():
    """임계가 실측 간극(건전 최대 1.11 / 확인 최소 1.30) 안에 있어야 한다.

    누가 '조용하게 만들려고' 임계를 올리면 여기서 걸린다 — 1.30 을 넘기는 순간 코드로 원인이
    확인된 R1 적용전 동어반복조차 통과시키게 되기 때문이다."""
    assert 1.11 < gate._TAUT_EXCESS_FLOOR < 1.30, (
        f"excess 임계 {gate._TAUT_EXCESS_FLOOR} 가 실측 간극 밖이다. "
        "위쪽으로 나가면 확인된 동어반복(R1 적용전 1.30)을 놓치고, "
        "아래쪽으로 나가면 건전축(R6 적용전 1.11)을 오탐한다.")
    assert 2.6 < gate._TAUT_Z_FLOOR < 11.4, (
        f"z 임계 {gate._TAUT_Z_FLOOR} 가 실측 간극(건전 2.6 / 확인 11.4) 밖이다.")


def test_healthy_axis_is_silent_on_live_data(rows):
    """건전 축은 원래 데이터에서 발화하지 않는다 (무조건 발화하는 고장 차단)."""
    red, census = _red_axes(rows)
    row = census[(MUTATE_AXIS, "적용전")]
    assert row["n"] >= gate._TAUT_MIN_CELLS, f"표본이 {row['n']} 칸뿐 — 시험이 성립하지 않는다"
    assert (MUTATE_AXIS, "적용전") not in red, (
        f"{MUTATE_AXIS}[적용전] 이 실데이터에서 동어반복으로 판정됐다 "
        f"(excess={row['excess']:.2f}, z={row['z']:.1f}). 대조군으로 쓰던 축이 되맞춰졌다는 뜻이다 "
        "— 임계를 고치지 말고 그 축의 파이프라인을 확인하라.")


@pytest.mark.parametrize("column,key", [("적용전", "값"), ("적용후", "값_적용후")])
def test_reconciling_a_healthy_axis_makes_it_fire(rows, column, key):
    """R6 을 인위적으로 되맞추면 발화한다 — **적용전·적용후 둘 다.**

    적용후를 같이 시험하는 이유: 이 저장소의 반복 사고가 '적용전만 배선하고 끝내는 것'이다.
    적용후 미러를 안 만들면 되맞춤이 적용후 컬럼에서만 일어났을 때 영원히 조용하다."""
    mutated = copy.deepcopy(rows)
    byq: dict[tuple, dict] = {}
    for r in mutated:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = r

    def num(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    forced = 0
    for m in byq.values():
        tgt = m.get(MUTATE_TARGET)
        if tgt is None:
            continue
        vals = {i: num(m.get(i, {}).get(key)) for i in MUTATE_TERMS}
        if any(v is None for v in vals.values()):
            continue
        if sum(1 for v in vals.values() if v != 0) < 2:
            continue
        tgt[key] = str(sum(s * vals[i] for i, s in MUTATE_TERMS.items()))
        forced += 1
    assert forced >= gate._TAUT_MIN_CELLS, f"되맞춘 셀이 {forced} 개뿐 — 시험이 성립하지 않는다"

    red, census = _red_axes(mutated)
    row = census[(MUTATE_AXIS, column)]
    assert (MUTATE_AXIS, column) in red, (
        f"{MUTATE_AXIS}[{column}] 을 {forced}칸 전부 항등식에 맞게 되맞췄는데 발화하지 않는다 "
        f"(정확0 {row['zeros']}/{row['n']} = {100*row['zero_rate']:.1f}%, "
        f"귀무 {100*row['null_rate']:.1f}%, excess {row['excess']:.2f}, z {row['z']:.1f}). "
        "임계가 느슨해졌거나 그 컬럼이 배선에서 빠졌다.")


# ---------------------------------------------------------------------------
# owner 승인 면제 (2026-08-21) — 상한 박제가 실제로 되돌아오는지
# ---------------------------------------------------------------------------
# 면제를 넣으면 그 축의 변이시험이 통째로 무력화되기 쉽다("발화 안 하니 통과"). 그래서 면제
# **그 자체**를 변이시험한다 — 박제 상한을 넘기면 RED 가 돌아와야 하고, 축이 수렴하면
# "이제 지워라" 가 나와야 한다. 둘 다 안 되면 면제는 그냥 blanket skip 이다.

def _findings_with_registry(census, registry, tol=None):
    """`_TAUT_EXEMPT` 를 일시 교체해 findings 를 다시 계산한다."""
    old_reg, old_tol = gate._TAUT_EXEMPT, gate._TAUT_PIN_EXCESS_TOL
    gate._TAUT_EXEMPT = registry
    if tol is not None:
        gate._TAUT_PIN_EXCESS_TOL = tol
    try:
        return gate._identity_tautology_findings(census)
    finally:
        gate._TAUT_EXEMPT, gate._TAUT_PIN_EXCESS_TOL = old_reg, old_tol


def test_exempt_registry_axes_actually_exist(rows):
    """등재된 축이 실제 축 목록에 있어야 한다 — 오타로 등재하면 면제가 조용히 안 걸린다."""
    census, _drift = gate._identity_tautology_census(rows)
    known = {(r["axis"], r["column"]) for r in census}
    ghost = sorted(set(gate._TAUT_EXEMPT) - known)
    assert not ghost, f"_TAUT_EXEMPT 에 실재하지 않는 축 {ghost}"


def test_exempt_axis_is_not_red_but_stays_flagged(rows):
    """면제 축은 push 를 막지 않지만 **동어반복이라는 표시는 유지**돼야 한다."""
    census, _drift = gate._identity_tautology_census(rows)
    red, _review, exempt = gate._identity_tautology_findings(census)
    red_axes = {(r["axis"], r["column"]) for r in red}
    exempt_axes = {(r["axis"], r["column"]) for r in exempt}
    for key in gate._TAUT_EXEMPT:
        assert key not in red_axes, f"{key} 는 면제인데 RED 로 남았다"
    assert exempt_axes, "면제 목록이 비었다 — 등재 축이 더는 발화하지 않으면 등재를 지워라"


def test_pin_drift_brings_the_red_back(rows):
    """박제 상한을 넘게 되맞춰지면 RED 가 돌아온다. 이게 안 되면 면제 = blanket skip."""
    census, _drift = gate._identity_tautology_census(rows)
    # 등재값보다 훨씬 낮은 상한으로 바꾼다 = "실측이 그만큼 더 되맞춰진" 상황과 동치.
    tightened = {k: {**v, "excess": 1.00} for k, v in gate._TAUT_EXEMPT.items()}
    red, _review, exempt = _findings_with_registry(census, tightened)
    drift = [r for r in red if r.get("rule") == "IDENTITY_TAUTOLOGY_PIN_DRIFT"]
    assert drift, (
        "박제 상한을 1.00 으로 낮췄는데 IDENTITY_TAUTOLOGY_PIN_DRIFT 가 안 났다 — "
        "면제가 실측을 다시 안 재고 있다"
    )
    assert not exempt, "상한을 넘겼는데도 면제로 남은 축이 있다"


def test_tolerance_is_not_wide_enough_to_swallow_a_reintroduced_rewrite(rows):
    """허용오차가 실측 되맞춤 폭(1.25 -> 1.84)을 삼키면 안 된다."""
    assert gate._TAUT_PIN_EXCESS_TOL < 0.59, (
        f"허용오차 {gate._TAUT_PIN_EXCESS_TOL} 가 너무 넓다 — R2 되맞춤 재유입 실측폭"
        f"(1.25 -> 1.84 = +0.59)을 통과시킨다"
    )


def test_converged_axis_tells_you_to_delete_the_exemption(rows):
    """축이 수렴해 발화가 멈추면 '등재를 지워라' 가 나와야 한다 — 면제가 영구 잔류하는 것 차단."""
    census, _drift = gate._identity_tautology_census(rows)
    healthy = next((r for r in census
                    if r["excess"] is not None and r["n"] >= gate._TAUT_MIN_CELLS
                    and not (r["excess"] >= gate._TAUT_EXCESS_FLOOR
                             and (r["z"] or 0) >= gate._TAUT_Z_FLOOR)), None)
    assert healthy is not None, "건전 축이 하나도 없다 — 대조군이 사라졌다"
    key = (healthy["axis"], healthy["column"])
    _red, review, _exempt = _findings_with_registry(
        census, {key: {"excess": 1.25, "z": 5.4, "n": healthy["n"], "zeros": healthy["zeros"]}})
    hits = [r for r in review if r.get("rule") == "IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY"
            and (r["axis"], r["column"]) == key]
    assert hits, f"{key} 는 발화하지 않는 축인데 면제 등재를 지우라는 review 가 안 나왔다"
