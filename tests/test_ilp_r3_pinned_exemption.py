# -*- coding: utf-8 -*-
"""`R3_PINNED_EXEMPTIONS` (AIG손해보험 KR0029 2024.4Q, owner 승인 2026-10-12)의 **변이시험**.

포트폴리오 검증기 `validate_insurance_liability_portfolio.py` 의 R3 「10배 규칙」은 종전에 등재부를 읽는 쪽이 없었다.
등재부만 있고 읽는 분기가 없으면 다음 라운드에 샌다 -- 그래서 이 파일은 읽는 쪽(`check_r3`)을 변이시킨다.
면제는 (회사,분기) 한 칸 + **값 박제**다: item8 이나 item20 이 움직이면 RED 가 돌아오고, 더는 필요 없는 면제는 RED(INERT)다.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_insurance_liability_portfolio as V  # noqa: E402

KEY = ("KR0029", "2024.4Q")
PIN = V.R3_PINNED_EXEMPTIONS[KEY]


def _run(item8, item20_mm, key=KEY, pins=None):
    by_cq = {key: {8: {"값": item8}}}
    reg = {key: item20_mm}
    f = {"RED": [], "YELLOW": [], "exceptions": []}
    V.check_r3(by_cq, reg, f, pins)
    return f


def test_registry_holds_exactly_the_approved_cell():
    assert set(V.R3_PINNED_EXEMPTIONS) == {KEY}
    assert PIN["item8_eok"] == 31.0 and abs(PIN["item20_mm"] - 291767.640554) < 1e-9


def test_pinned_cell_is_exempt_and_printed():
    f = _run(PIN["item8_eok"], PIN["item20_mm"])
    assert f["RED"] == [] and len(f["exceptions"]) == 1 and "pinned" in f["exceptions"][0]


def test_control_without_registry_the_same_cell_is_red():
    f = _run(PIN["item8_eok"], PIN["item20_mm"], pins={})
    assert len(f["RED"]) == 1 and "gap > 10x" in f["RED"][0] and f["exceptions"] == []


def test_item8_drift_brings_red_back():
    f = _run(PIN["item8_eok"] + 0.5, PIN["item20_mm"])
    assert any(r.startswith("R3_PIN_DRIFT") for r in f["RED"]) and f["exceptions"] == []


def test_item20_drift_brings_red_back():
    f = _run(PIN["item8_eok"], PIN["item20_mm"] + 5.0)
    assert any(r.startswith("R3_PIN_DRIFT") for r in f["RED"]) and f["exceptions"] == []


def test_other_company_same_numbers_is_not_exempt():
    f = _run(PIN["item8_eok"], PIN["item20_mm"], key=("KR0001", "2024.4Q"))
    assert len(f["RED"]) == 1 and f["exceptions"] == []


def test_other_quarter_same_company_is_not_exempt():
    f = _run(PIN["item8_eok"], PIN["item20_mm"], key=("KR0029", "2025.1Q"))
    assert len(f["RED"]) == 1 and f["exceptions"] == []


def test_inert_pin_is_red():
    # item8 이 정상(10배 안)이 되면 면제가 죽은 면제 -> RED.
    f = _run(2000.0, PIN["item20_mm"], pins={KEY: dict(PIN, item8_eok=2000.0)})
    assert any(r.startswith("R3_EXEMPTION_INERT") for r in f["RED"])


def test_negative_slack_branch_is_also_pin_guarded():
    # item20 < item8 (음의 간극) RED 도 같은 읽는 쪽을 지난다: 박제 값이 맞으면 면제, 아니면 RED.
    pins = {KEY: {"item8_eok": 1000.0, "item20_mm": 50000.0, "reason": "x"}}
    assert _run(1000.0, 50000.0, pins=pins)["RED"] == []
    assert any(r.startswith("R3_PIN_DRIFT") for r in _run(1000.0, 49000.0, pins=pins)["RED"])
    assert len(_run(1000.0, 50000.0, pins={})["RED"]) == 1


def test_reader_mutation_ignoring_registry_is_detected(monkeypatch):
    # 읽는 쪽 변이: check_r3 가 등재부를 무시하도록 바꾸면 이 파일의 핵심 단언이 깨진다.
    monkeypatch.setattr(V, "R3_PINNED_EXEMPTIONS", {})
    f = _run(PIN["item8_eok"], PIN["item20_mm"])
    assert len(f["RED"]) == 1 and f["exceptions"] == []


def test_live_master_has_no_r3_red_and_pin_is_live():
    rows = V.load_master()
    by_cq = {}
    for r in rows:
        by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r
    f = {"RED": [], "YELLOW": [], "exceptions": []}
    V.check_r3(by_cq, V.load_item20_registry(), f)
    assert f["RED"] == [], f["RED"]
    assert any("KR0029 2024.4Q" in e for e in f["exceptions"])
