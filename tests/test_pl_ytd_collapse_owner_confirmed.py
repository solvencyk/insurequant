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

# owner 승인 2026-10-12: 재보사 「인쇄된 0」 7칸(마스터에서 보류 중, 복원은 parser-ifrs17 의 reinsurer_resweep_pl_followup.py --restore7)
SEVEN = [
    ("뮌헨재보험", "2023.4Q", "투자손익"),
    ("알지에이리인슈어런스", "2023.2Q", "영업외손익"),
    ("알지에이리인슈어런스", "2025.3Q", "영업외손익"),
    ("제네럴재보험", "2024.3Q", "영업외손익"),
    ("제네럴재보험", "2025.3Q", "영업외손익"),
    ("퍼시픽라이프리", "2023.3Q", "영업외손익"),
    ("퍼시픽라이프리", "2025.3Q", "영업외손익"),
]


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
    approved = {
        KEY,                                                    # owner 2026-10-10 (예별 2025.3Q, 보고주체 단절)
        ("스위스리아시아", "2023.2Q", "법인세"),                  # owner 2026-10-11 (원문에 0 인쇄)
        ("퍼시픽라이프리", "2024.4Q", "법인세"),                  # owner 2026-10-11 (감사보고서 당기법인세 '-')
        ("퍼시픽라이프리", "2025.4Q", "법인세"),
        *SEVEN,                                                 # owner 2026-10-12 (재보사 인쇄된 0 7칸)
    }
    assert len(ytd) == len(set(ytd)) and set(ytd) == approved, (
        f"등재 범위가 owner 승인(2026-10-10 1칸 + 2026-10-11 3칸 + 2026-10-12 7칸)과 다르다: {sorted(ytd)}")


def test_every_registered_cell_is_reconfirmed_against_its_source():
    """등재 11칸 전부가 라이브 마스터·원문 PDF 로 재확인된다 -- 값/마커가 어긋난 칸이 하나라도 있으면 RED 가 돌아와 깨진다.
    (데이터가 채워져 붕괴가 사라진 칸은 게이트가 INERT YELLOW 로 알리는 일이라 여기서는 막지 않는다.)"""
    import validate_master_tables as VM
    pl = VM.load_long(VM.PL_PATH)
    env = _Env()
    env.pl = pl
    env.wf = {}
    res = dc.GateResult()
    _ytd_block(res, env)
    reds = [(f.company, f.quarter, f.message) for f in res.findings
            if f.severity == "RED" and f.rule == "PL_YTD_COLLAPSE_TO_ZERO"]
    assert not reds, reds
    seen = {(f.company, f.quarter) for f in res.findings
            if f.rule in ("PL_YTD_COLLAPSE_OWNER_CONFIRMED", "PL_YTD_COLLAPSE_CONFIRMED_INERT",
                          "PL_YTD_COLLAPSE_CONFIRMED_PENDING")}
    assert seen >= {("스위스리아시아", "2023.2Q"), ("퍼시픽라이프리", "2024.4Q"), ("퍼시픽라이프리", "2025.4Q"),
                    ("예별손해보험", "2025.3Q")} | {(c, q) for c, q, _i in SEVEN}, sorted(seen)


# ---------------------------------------------------------------------------------------------------
# 읽는 쪽 -- 7칸이 마스터에 복원됐을 때(지금은 보류 중) 게이트가 면제를 정말 읽는지, 복원을 가정해 시뮬레이션한다
# ---------------------------------------------------------------------------------------------------
def _live_pl_with_seven(value=0.0, skip=()):
    import validate_master_tables as VM
    pl = VM.load_long(VM.PL_PATH)
    pl = {k: dict(v) for k, v in pl.items()}
    for co, q, item in SEVEN:
        if (co, q, item) in skip:
            continue
        pl.setdefault((co, q), {})[item] = value
    return pl


def _seven_findings(pl, monkeypatch=None, cells=None):
    env = _Env()
    env.pl = pl
    env.wf = {}
    if monkeypatch is not None and cells is not None:
        monkeypatch.setattr(dc, "_ytd_collapse_confirmed_cells", lambda e: cells)
    res = dc.GateResult()
    _ytd_block(res, env)
    return res


def test_seven_restored_cells_are_exempt_when_registered():
    """등재 7칸을 0.0 으로 복원하면(가정) RED 0 · OWNER_CONFIRMED YELLOW 7 -- 읽는 분기가 등재부를 실제로 읽는다."""
    res = _seven_findings(_live_pl_with_seven())
    reds = [f for f in res.findings if f.severity == "RED" and f.rule == "PL_YTD_COLLAPSE_TO_ZERO"]
    assert not reds, [(f.company, f.quarter, f.message) for f in reds]
    ok = {(f.company, f.quarter) for f in res.findings if f.rule == "PL_YTD_COLLAPSE_OWNER_CONFIRMED"}
    assert {(c, q) for c, q, _i in SEVEN} <= ok, sorted(ok)


def test_seven_restored_cells_are_red_without_registration(monkeypatch):
    """대조군: 등재부가 비면 같은 7칸이 정확히 RED 7 -- 위 시험이 「애초에 붕괴로 안 잡혀서」 통과한 것이 아님을 보인다."""
    res = _seven_findings(_live_pl_with_seven(), monkeypatch, cells={})
    reds = {(f.company, f.quarter) for f in res.findings if f.severity == "RED" and f.rule == "PL_YTD_COLLAPSE_TO_ZERO"}
    seven = {(c, q) for c, q, _i in SEVEN}
    assert seven <= reds, sorted(seven - reds)
    # 등재부를 비우면 이전 승인 4칸도 같이 RED 로 돌아온다(등재가 면제의 유일한 근거) -- 그 밖의 붕괴는 없다
    assert reds - seven == {("스위스리아시아", "2023.2Q"), ("퍼시픽라이프리", "2024.4Q"), ("퍼시픽라이프리", "2025.4Q"),
                            ("예별손해보험", "2025.3Q")}, sorted(reds - seven)


def test_seven_registration_does_not_cover_another_item_or_quarter():
    """등재는 (회사,분기,항목) 한 칸씩이다 -- 같은 회사의 다른 항목/분기 0 붕괴는 면제되지 않는다."""
    pl = _live_pl_with_seven()
    # 제네럴 2025.2Q 영업외손익을 직전분기 비영 -> 0 으로 만든 가짜 붕괴(등재 없음)
    pl[("제네럴재보험", "2025.2Q")] = dict(pl.get(("제네럴재보험", "2025.2Q"), {}), 영업외손익=0.0)
    pl[("제네럴재보험", "2025.1Q")] = dict(pl.get(("제네럴재보험", "2025.1Q"), {}), 영업외손익=12.0)
    res = _seven_findings(pl)
    reds = {(f.company, f.quarter) for f in res.findings if f.severity == "RED" and f.rule == "PL_YTD_COLLAPSE_TO_ZERO"}
    assert reds == {("제네럴재보험", "2025.2Q")}, sorted(reds)


@pytest.mark.parametrize("co,q,item", SEVEN)
def test_seven_value_drift_revives_red_or_inert(co, q, item):
    """복원 값이 0.0 이 아니면(예: 5.0) 붕괴 자체가 없으니 INERT YELLOW 로 등재를 풀라고 알린다 -- RED 는 아니다."""
    res = _seven_findings(_live_pl_with_seven(value=5.0, skip={(c2, q2, i2) for c2, q2, i2 in SEVEN if (c2, q2, i2) != (co, q, item)}))
    assert ("YELLOW", "PL_YTD_COLLAPSE_CONFIRMED_INERT") in {(f.severity, f.rule) for f in res.findings
                                                              if (f.company, f.quarter) == (co, q)}
    assert not [f for f in res.findings if f.severity == "RED" and f.rule == "PL_YTD_COLLAPSE_TO_ZERO"]


def test_registered_but_not_yet_restored_cells_are_pending_not_inert():
    """마스터에 셀이 아직 없는(복원 대기) 등재는 PENDING 이다 -- INERT(「등재를 풀어라」)로 읽히면 방금 승인된 등재를 풀게 된다."""
    import validate_master_tables as VM
    pl = VM.load_long(VM.PL_PATH)
    live_has = [(c, q, i) for c, q, i in SEVEN if i in pl.get((c, q), {})]
    res = _seven_findings(pl)
    by_rule = {}
    for f in res.findings:
        if f.rule in ("PL_YTD_COLLAPSE_CONFIRMED_PENDING", "PL_YTD_COLLAPSE_CONFIRMED_INERT", "PL_YTD_COLLAPSE_OWNER_CONFIRMED"):
            by_rule.setdefault(f.rule, set()).add((f.company, f.quarter))
    absent = {(c, q) for c, q, i in SEVEN} - {(c, q) for c, q, i in live_has}
    assert absent <= by_rule.get("PL_YTD_COLLAPSE_CONFIRMED_PENDING", set()), sorted(absent)
    assert not (absent & by_rule.get("PL_YTD_COLLAPSE_CONFIRMED_INERT", set()))


def test_pending_turns_into_owner_confirmed_once_restored():
    """같은 7칸을 0.0 으로 복원하면 PENDING 이 사라지고 OWNER_CONFIRMED 로 바뀐다."""
    res = _seven_findings(_live_pl_with_seven())
    pend = {(f.company, f.quarter) for f in res.findings if f.rule == "PL_YTD_COLLAPSE_CONFIRMED_PENDING"}
    assert not ({(c, q) for c, q, _i in SEVEN} & pend)

