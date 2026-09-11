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


def test_the_kr0003_2026q1_regression_pattern_would_still_be_caught():
    """KR0003 2026.1Q 는 더 이상 `_KNOWN` 에 없다 — 2026-09-11 REOPEN 조사
    (inbox 20260911T1407Z) 로 회귀가 아니라 데이터가 실제로 고쳐진 것임을 확인했다:
    발행사가 2026-09-03 원문을 재제출해(commit 66cfa0b) TFI 표가 더는 전기(2025.4Q)
    재게시가 아니다. `detect()` 를 재제출 직전 스냅샷(git show 7c33aae:kics_disclosure.json)
    에 돌리면 지금도 fingerprint A 가 잡힌다 — 탐지기는 살아 있다, 다만 그 스냅샷은
    이력일 뿐 라이브 마스터가 아니라 이 테스트 스위트가 직접 참조할 수 없다.

    그래서 "탐지기가 여전히 잡는다"를 **라이브 히트가 아니라 그 정확한 옛 패턴의 합성
    재현**으로 증명한다: KR0003 2026.1Q 의 item48 을 2025.4Q(직전분기) SCR x 50% 로
    되돌리면(2026-09-03 이전 실제 값과 동일한 오염) 지문 A 가 다시 잡혀야 한다. 잡히지
    않으면 탐지기가 죽은 것이다.
    """
    m = _mod()
    recs = _records()
    prev14 = _find(recs, "KR0003", "2025.4Q", 14)
    cur14 = _find(recs, "KR0003", "2026.1Q", 14)
    r48 = _find(recs, "KR0003", "2026.1Q", 48)
    assert prev14 and cur14 and r48, "KR0003 2025.4Q/2026.1Q 입력이 마스터에 없다"
    p, c = m._f(prev14["값"]), m._f(cur14["값"])
    assert p is not None and c is not None and abs(c - p) > m.TOL, (
        "KR0003 의 SCR 이 분기 간 안 바뀐다 — 이 회귀 재현의 전제(판별 가능 구간)가 깨졌다"
    )

    baseline = {(h["code"], h["quarter"], h["column"], h["fingerprint"])
                for h in m.detect(recs)}
    r48["값"] = f"{p * 0.5:.2f}"  # 2026-09-03 이전 실제로 관측됐던 것과 동일한 오염
    mutated = {(h["code"], h["quarter"], h["column"], h["fingerprint"])
               for h in m.detect(recs)}

    assert ("KR0003", "2026.1Q", "값", "A") in mutated - baseline, (
        "KR0003 2026.1Q 의 2026-09-03 이전 실제 결함 패턴(item48 = 직전분기 SCR x 50%)을 "
        "재현했는데 지문 A 가 못 잡았다 — 탐지기 회귀"
    )


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
