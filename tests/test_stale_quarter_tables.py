# -*- coding: utf-8 -*-
"""`scripts/validate_stale_quarter_tables.py` 변이시험.

이 저장소는 "게이트에 배선했다" 와 "실제로 잡는다" 를 여러 번 혼동했다. 탐지기가
정상 데이터에서 조용한 것만으로는 아무것도 증명하지 못하므로, **스테일 표를 인위적으로
심어 넣고 실제로 걸리는지** 를 확인한다.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_stale_quarter_tables.py"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="slim 워크트리")


def _mod():
    spec = importlib.util.spec_from_file_location("_stale_quarter", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _records():
    p = ROOT / "kics_disclosure.json"
    if not p.exists():
        pytest.skip("kics_disclosure.json 없음")
    return json.loads(p.read_text(encoding="utf-8"))


def test_live_master_has_only_known_hits():
    """라이브 마스터에서는 등재된 것 말고 히트가 없어야 한다."""
    m = _mod()
    hits = m.detect(_records())
    unknown = [h for h in hits
               if (h["code"], h["quarter"], h["column"]) not in m._KNOWN]
    assert not unknown, f"미등재 스테일 표: {unknown}"


def test_known_hit_still_fires():
    """등재부가 박제한 KR0003 2026.1Q 를 탐지기가 여전히 잡는가.

    잡히지 않게 되면 탐지기가 죽었거나 데이터가 바뀐 것이다 — 둘 다 알아야 한다.
    """
    m = _mod()
    hits = {(h["code"], h["quarter"], h["column"]) for h in m.detect(_records())}
    assert ("KR0003", "2026.1Q", "값") in hits


def _find(recs, code, q, item):
    for r in recs:
        if r["원보험사코드"] == code and r["공시분기"] == q and r["항목번호"] == item:
            return r
    return None


@pytest.mark.parametrize("victim", [("KR0001", "2026.2Q"), ("KR0069", "2026.2Q")])
def test_mutation_fingerprint_a_fires(victim):
    """item48 을 직전분기 SCR 기준으로 갈아끼우면 지문 A 가 잡아야 한다."""
    m = _mod()
    code, q = victim
    recs = _records()
    prev_q = m._prev(q)
    cur14 = _find(recs, code, q, 14)
    prev14 = _find(recs, code, prev_q, 14)
    r48 = _find(recs, code, q, 48)
    if not (cur14 and prev14 and r48):
        pytest.skip(f"{code} {q} 입력 부족")
    c, p = m._f(cur14["값"]), m._f(prev14["값"])
    if c is None or p is None or abs(c - p) <= m.TOL:
        pytest.skip(f"{code} {q} SCR 변화 없음 — 판별 불가 구간")

    baseline = {(h["code"], h["quarter"], h["column"], h["fingerprint"])
                for h in m.detect(recs)}
    r48["값"] = f"{p * 0.5:.2f}"          # 직전분기 한도로 오염
    mutated = {(h["code"], h["quarter"], h["column"], h["fingerprint"])
               for h in m.detect(recs)}

    assert (code, q, "값", "A") in mutated - baseline, (
        f"{code} {q} 의 item48 을 직전분기 SCR x 50% 로 심었는데 지문 A 가 못 잡았다"
    )
