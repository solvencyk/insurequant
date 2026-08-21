#!/usr/bin/env python3
"""변이시험 — 신규 룰 `OTHER_CAPITAL_CHILDREN_SUM` 이 흥국생명 KR0071 2023.3Q 를 **실제로**
잡는지, 그리고 **룰을 끄면 아무도 안 잡는지** 확인한다 (티켓 20260821T1100Z 수용기준 ①).

우연히 통과하는 mutation test 는 없는 것만 못하다 — 그래서 두 방향을 다 본다:
  A. 룰 ON  → 그 (회사,분기) 가 게이트 리포트에 나타난다.
  B. 룰 OFF → 게이트 리포트 **전 섹션**을 훑어 그 (회사,분기) 를 **결함으로 지목한 것이 하나도
     없다**. 판정 기준은 "언급 0" 이 아니라 "**실패 0**" 이다 — 룰엔진 findings 에는 통과
     기록(GREEN/SKIP)이 같은 (회사,분기) 로 남으므로, 언급을 세면 시험이 자기 기준에 걸려
     항상 FAIL 한다(첫 판에 실제로 그렇게 틀렸다). 통과 기록은 오히려 **증거**다: 기존 룰
     12개가 전부 GREEN 이라는 것이 곧 "아무도 이 오류를 못 본다" 는 뜻이다.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/mutation_test_item23_rule.py
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_kics_disclosure as G  # noqa: E402

TARGET = ("KR0071", "2023.3Q")
REPORT = ROOT / "artifacts" / "kics_validation" / "report_latest.json"


def _hits(obj, path="report"):
    """리포트 트리 전체에서 TARGET (회사,분기) 를 가리키는 dict 노드를 모은다.
    섹션 이름을 하드코딩하지 않는다 — 새 검사가 늘어도 이 시험이 같이 자란다."""
    out = []
    if isinstance(obj, dict):
        code = obj.get("code") or obj.get("원보험사코드")
        q = obj.get("quarter") or obj.get("공시분기")
        if code == TARGET[0] and q == TARGET[1]:
            out.append((path, obj))
        for k, v in obj.items():
            out.extend(_hits(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_hits(v, f"{path}[{i}]"))
    return out


def run_gate() -> list:
    buf = io.StringIO()
    with redirect_stdout(buf):
        G.main()
    return _hits(json.loads(REPORT.read_text(encoding="utf-8")))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(f"변이시험 대상: {TARGET[0]} {TARGET[1]} (흥국생명 item24=8,313 날조)")

    # --- A. 룰 ON -----------------------------------------------------------
    on = run_gate()
    on_paths = sorted({p.rsplit("[", 1)[0] for p, _ in on})
    on_new = [(p, o) for p, o in on if "other_capital" in p]
    print(f"\n[A] 룰 ON  — 리포트에서 이 (회사,분기) 를 언급한 섹션 {len(on_paths)}개:")
    for p in on_paths:
        print(f"      {p}")
    print(f"    신규 룰 섹션 히트: {len(on_new)}")
    for _p, o in on_new:
        print(f"      {o}")

    # --- B. 룰 OFF (변이: 검사를 죽인다) ------------------------------------
    orig = G._other_capital_children_sum
    G._other_capital_children_sum = lambda records: ([], Counter())
    try:
        off = run_gate()
    finally:
        G._other_capital_children_sum = orig
    off_paths = sorted({p.rsplit("[", 1)[0] for p, _ in off})
    print(f"\n[B] 룰 OFF — 리포트에서 이 (회사,분기) 를 언급한 섹션 {len(off_paths)}개:")
    for p in off_paths:
        print(f"      {p}")

    # 룰 OFF 상태의 히트를 '통과 기록' 과 '결함 지목' 으로 가른다.
    off_engine = [(p, o) for p, o in off if p.startswith("report.findings")]
    off_defect = [(p, o) for p, o in off if not p.startswith("report.findings")]
    off_engine_red = [(p, o) for p, o in off_engine if o.get("status") == "RED"]
    st_off = Counter(o.get("status") for _p, o in off_engine)
    print(f"    그중 룰엔진 findings {len(off_engine)}건의 상태: {dict(st_off)}")
    print(f"    그중 결함 지목 섹션 히트: {len(off_defect)}건")

    # --- 판정 ---------------------------------------------------------------
    ok_a = len(on_new) == 1
    ok_b = not off_defect and not off_engine_red
    print("\n판정:")
    print(f"  A 룰 ON  에서 신규 룰이 정확히 1건 검출: {'PASS' if ok_a else 'FAIL'}")
    print(f"  B 룰 OFF 에서 **어느 검사도 결함으로 지목하지 못함**: {'PASS' if ok_b else 'FAIL'} "
          f"(엔진 RED {len(off_engine_red)} · 결함섹션 {len(off_defect)})")
    for p, o in off_engine_red + off_defect:
        print(f"      잔여 결함지목: {p} {o}")
    print(f"  → 기존 룰 {len(off_engine)}개가 이 셀을 전부 {dict(st_off)} 로 통과시킨다 "
          f"= 이 오류를 보는 검사가 종전엔 하나도 없었다.")
    print("\nRESULT:", "PASS" if (ok_a and ok_b) else "FAIL")
    return 0 if (ok_a and ok_b) else 2


if __name__ == "__main__":
    raise SystemExit(main())
