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
    red, _review = gate._identity_tautology_findings(census)
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
