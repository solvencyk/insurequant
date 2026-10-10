# -*- coding: utf-8 -*-
"""`PL_YTD_COLLAPSE_TO_ZERO` owner 확정 셀 경로의 **변이시험** (owner 결정 2026-10-10).

예별손해보험 2025.3Q 법인세 0.0 은 신설법인 제1기(2025.6.16~9.30) 손익계산서의 인쇄값이라 붕괴가 아니라
보고주체 단절이다. 등재는 `data/_gold/user_pl_confirmed_cells.json` 의 셀(rule=PL_YTD_COLLAPSE_TO_ZERO,
값 박제 + verify 마커)이고, 데이터계약 게이트는 **값 일치 + 인용 문구 재확인** 둘 다 통과할 때만 RED 를
YELLOW 로 바꿔 인쇄한다. 여기서는 등재 칸을 흔들면 RED 로 돌아오는 것을 증명한다(디스크는 안 건드린다).
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

import validate_data_contract as dc  # noqa: E402

KEY = ("예별손해보험", "2025.3Q", "법인세")


class _Env:
    inject: dict = {}


def _run(pl, monkeypatch, cells=None, confirmed=None):
    if cells is not None:
        monkeypatch.setattr(dc, "_ytd_collapse_confirmed_cells", lambda env: cells)
    if confirmed is not None:
        monkeypatch.setattr(dc, "_load_owner_confirmed", lambda: confirmed)
    env = _Env()
    env.pl = pl
    env.wf = {}
    res = dc.GateResult()
    _ytd_block(res, env)
    return res


def _ytd_block(res, env):
    """`check_census` 의 YTD 블록과 같은 함수들을 같은 순서로 부른다 — 소스에서 블록을 그대로 실행한다."""
    import inspect
    import textwrap
    src = inspect.getsource(dc.check_census)
    start = src.index("    ytd_ok = _ytd_collapse_confirmed_cells(env)")
    end = src.index("    # CSM 상대규모 plausibility")
    block = textwrap.dedent(src[start:end])
    exec(block, dict(vars(dc)), {"res": res, "env": env})


@pytest.fixture(scope="module")
def live_cell():
    d = json.loads((ROOT / "data" / "_gold" / "user_pl_confirmed_cells.json").read_text(encoding="utf-8"))
    hit = [c for c in d["cells"] if (c["company"], c["quarter"], c["item"]) == KEY]
    assert len(hit) == 1 and hit[0].get("rule") == "PL_YTD_COLLAPSE_TO_ZERO"
    return hit[0]


def _pl(v3=0.0):
    return {("예별손해보험", "2025.2Q"): {"법인세": 8079.681}, ("예별손해보험", "2025.3Q"): {"법인세": v3}}


def _cells(cell):
    return {(dc._norm_ws(KEY[0]), KEY[1], dc._norm_ws(KEY[2])): cell}


def _rules(res):
    return {(f.severity, f.rule) for f in res.findings}


def test_registered_cell_is_yellow_not_red(live_cell, monkeypatch):
    res = _run(_pl(), monkeypatch, cells=_cells(live_cell))
    assert ("YELLOW", "PL_YTD_COLLAPSE_OWNER_CONFIRMED") in _rules(res)
    assert not res.red


def test_unregistered_collapse_stays_red(monkeypatch):
    res = _run(_pl(), monkeypatch, cells={})
    assert ("RED", "PL_YTD_COLLAPSE_TO_ZERO") in _rules(res)


def test_value_pin_mismatch_revives_red(live_cell, monkeypatch):
    bad = {(  "PL_breakdown", dc._norm_ws(KEY[0]), KEY[1], dc._norm_ws(KEY[2])): 123.0}
    res = _run(_pl(), monkeypatch, cells=_cells(live_cell), confirmed=(bad, 2.0, 0.01))
    assert any(f.severity == "RED" and "등재 값" in f.message for f in res.findings)


@pytest.mark.parametrize("marker", ["제13(당) 3분기", "Ⅶ. 법인세비용 8,079,681,110"])
def test_evidence_contradicted_revives_red(live_cell, monkeypatch, marker):
    cell = copy.deepcopy(live_cell)
    cell["verify"]["present_markers"] = list(cell["verify"]["present_markers"]) + [marker]
    res = _run(_pl(), monkeypatch, cells=_cells(cell))
    assert any(f.severity == "RED" and "재확인 실패" in f.message for f in res.findings)


def test_missing_verify_block_revives_red(live_cell, monkeypatch):
    cell = copy.deepcopy(live_cell)
    cell.pop("verify")
    res = _run(_pl(), monkeypatch, cells=_cells(cell))
    assert any(f.severity == "RED" and "verify 마커" in f.message for f in res.findings)


def test_inert_registration_is_reported(live_cell, monkeypatch):
    """붕괴가 사라지면(값이 채워지면) 등재가 무용해졌다고 매 실행 알린다."""
    res = _run(_pl(v3=12.0), monkeypatch, cells=_cells(live_cell))
    assert ("YELLOW", "PL_YTD_COLLAPSE_CONFIRMED_INERT") in _rules(res)
    assert not res.red


def test_only_owner_approved_cells_use_this_path():
    d = json.loads((ROOT / "data" / "_gold" / "user_pl_confirmed_cells.json").read_text(encoding="utf-8"))
    ytd = [(c["company"], c["quarter"], c["item"]) for c in d["cells"] if c.get("rule") == "PL_YTD_COLLAPSE_TO_ZERO"]
    assert ytd == [KEY], f"등재 범위가 owner 승인(2026-10-10, 1칸)과 다르다: {ytd}"
