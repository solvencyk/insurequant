# -*- coding: utf-8 -*-
"""분기 지평 트립와이어 — "게이트가 최신 분기를 **순회조차 안 한다**" 를 기계가 막는다.

왜 있나 (2026-08-29, `inbox/validation/20260829T1910Z`)
------------------------------------------------------
게이트 세 곳이 각자 분기 목록을 리터럴로 들고 있었고 셋 다 `2026.1Q` 에서 끝나 있었다.
2026.2Q 데이터를 라이브에 배포한 날, `validate_master_tables` 의 coverage census · qoq ·
spike · wfy · continuity 와 `validate_data_contract` 의 census RED 스코프가 **그 분기를 한
번도 보지 않았다.** SUMMARY 의 `RED=0` 은 그 분기에 대해서는 "검사했더니 깨끗" 이 아니라
**"안 봤다"** 였고, 실제로 `흥국화재 2026.2Q` PL 항목 2/8/12/13/14 결측이 그 사각에
숨어 있었다(직전 2026.1Q 는 다섯 항목 전부 정상 = 최신 분기 회귀).

**하드코딩 자체가 재발 구조다.** 분기가 늘 때마다 사람이 세 곳을 고쳐야 하면 다음에 또
빠진다. 그래서 지평은 `scripts/_quarter_horizon.py` 가 마스터에서 파생하고, 이 테스트가
① 파생된 지평이 실제 마스터 최신 분기를 품는지 ② 게이트가 자기 리터럴 지평을 다시
심지 않았는지 두 가지를 강제한다.

이 테스트는 `scripts/prepush_check.py` 의 오프라인 테스트 목록에 배선돼 있다 — 배선
안 하면 "룰은 있는데 아무도 안 돌린다"(CLAUDE.md 의 honor-system 사고)로 돌아간다.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from _quarter_horizon import (  # noqa: E402
    HORIZON_SOURCES,
    QUARTER_FLOOR,
    display_quarters,
    latest_quarter,
    quarter_horizon,
)

QRE = re.compile(r"^20\d\d\.[1-4]Q$")
_QIN_JSON = re.compile(rb'"\xea\xb3\xb5\xec\x8b\x9c\xeb\xb6\x84\xea\xb8\xb0"\s*:\s*"(20\d\d\.[1-4]Q)"')


def _k(q: str) -> tuple[int, int]:
    return int(q[:4]), int(q[5])


# ---------------------------------------------------------------------------
# 1. 파생 지평이 마스터의 최신 분기를 실제로 품는가
# ---------------------------------------------------------------------------
def test_horizon_reaches_every_master_high_water():
    """어떤 마스터에 있는 분기가 지평 밖이면, 그 분기는 어떤 축도 순회하지 않는다."""
    qs = set(quarter_horizon())
    missed = {}
    for name in HORIZON_SOURCES:
        p = ROOT / name
        if not p.exists():
            continue
        found = {q.decode() for q in _QIN_JSON.findall(p.read_bytes())}
        out = {q for q in found if q not in qs and _k(q) >= _k(QUARTER_FLOOR)}
        if out:
            missed[name] = sorted(out)
    assert not missed, f"마스터에 있는데 지평 밖인 분기: {missed}"


# ---------------------------------------------------------------------------
# 2. 각 게이트의 지평 상수가 최신 분기를 담고 있는가  ← 이 사고를 당일에 잡는 테스트
# ---------------------------------------------------------------------------
GATE_HORIZONS = [
    ("validate_master_tables", "QS", "coverage census · qoq · spike · wfy · continuity"),
    ("validate_kics_rate_sensitivity", "ALL_Q", "RS4 커버리지 census"),
]


@pytest.mark.parametrize("mod_name,attr,what", GATE_HORIZONS, ids=[m for m, _, _ in GATE_HORIZONS])
def test_gate_horizon_includes_latest_quarter(mod_name, attr, what):
    import importlib

    mod = importlib.import_module(mod_name)
    horizon = list(getattr(mod, attr))
    latest = latest_quarter()
    assert latest in horizon, (
        f"{mod_name}.{attr} 가 최신 분기 {latest} 를 포함하지 않는다 → {what} 가 그 분기를 "
        f"순회조차 하지 않는다(= RED 0 은 '안 봤다'는 뜻). 현재 끝={horizon[-1]}"
    )


def test_data_contract_red_scope_includes_latest_quarter():
    """`_DISPLAY_QUARTERS` 는 census RED 의 **발화 스코프**다. 최신 분기가 빠지면 결측을
    찾아내도 RED 로 올라오지 않는다(2026-08-29: 자물쇠가 QS 와 직렬 두 개였다)."""
    import validate_data_contract as dc

    latest = latest_quarter()
    assert latest in dc._DISPLAY_QUARTERS, (
        f"_DISPLAY_QUARTERS 에 최신 분기 {latest} 가 없다 — 그 분기의 census RED 은 "
        f"발화 자체가 막힌다. 현재={sorted(dc._DISPLAY_QUARTERS)}"
    )


def test_display_quarters_still_reproduce_the_owner_set():
    """owner 스코프(2026-06-20)의 7개를 파생 규칙이 그대로 재현하는지 — 규칙을 데이터
    파생으로 바꾸면서 과거 스코프를 조용히 넓히지 않았다는 회귀 가드."""
    owner_7 = {"2023.4Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"}
    derived = {q for q in display_quarters() if _k(q) <= _k("2026.1Q")}
    assert derived == owner_7, f"파생 스코프가 owner 7개와 다르다: {sorted(derived)}"


# ---------------------------------------------------------------------------
# 3. 게이트가 자기 리터럴 지평을 다시 심지 않았는가
# ---------------------------------------------------------------------------
GATE_FILES = sorted(
    [p for p in (ROOT / "scripts").glob("validate_*.py")]
    + [ROOT / "scripts" / "prepush_check.py", ROOT / "scripts" / "_quarter_horizon.py"]
)


def _literal_horizons(path: Path) -> list[tuple[int, list[str]]]:
    """`QUARTER_FLOOR` 에서 시작하는 분기 리터럴 컬렉션(=재타이핑된 지평)을 찾는다.

    회사·분기 예외 등재부는 `("KR0003", "2026.1Q")` 꼴의 튜플이라 걸리지 않고,
    `ZLEG_LEGIT_CQ` 처럼 하한이 아닌 데서 시작하는 구간 목록도 걸리지 않는다.
    걸리는 것은 "2023.1Q 부터 쭉 적어 내려간 목록" 하나뿐이다.
    """
    hits = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            continue
        elts = node.elts
        if len(elts) < 4:
            continue
        if not all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in elts):
            continue
        vals = [e.value for e in elts]
        if not all(QRE.match(v) for v in vals):
            continue
        if min(vals) == QUARTER_FLOOR:
            hits.append((node.lineno, vals))
    return hits


@pytest.mark.parametrize("path", GATE_FILES, ids=[p.name for p in GATE_FILES])
def test_no_gate_retypes_the_quarter_horizon(path):
    hits = _literal_horizons(path)
    assert not hits, (
        f"{path.name} 에 손으로 적은 분기 지평이 있다 {hits} — 분기가 늘 때마다 사람이 "
        f"고쳐야 하는 구조라 다음 분기에 또 빠진다. "
        f"`from _quarter_horizon import quarter_horizon` 로 파생할 것."
    )
