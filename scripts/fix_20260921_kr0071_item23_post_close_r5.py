"""Guarded cell-level fix: KR0071(흥국생명) item23(기타요구자본) 값_적용후 — R5 후 항등식 재폐쇄.

Ticket: inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md §B
Follows: scripts/fix_20260921_item14_post_backsolve.py (item14 후 30칸을 원문 헤드라인 정수로 정정).

Why item23 (not 15, not 22):
  KR0071 은 ②(장수·사업비·해지·대재해) + ③(주식위험) 다중경과조치사. 결합 적용후 15/22/23 은
  어느 표에도 인쇄되지 않는다(②·③ 세부표는 각 조치 단독 효과만). 마스터의 적용후 15~23 은 따라서
  전부 추정치이고, 그중
    - item15 후 = mmult(17..21 후) — 17후(②표 인쇄값)·19후(③표 인쇄값)·18/20/21후(불변)를 규제
      상관행렬로 결합한 값. 게이트 '적용후 mmult' 축이 검산하며 현재 통과. 건드리지 않는다.
    - item16 후 = sum(17..21 후) − 15 후 (R6). 15 를 안 건드리므로 그대로.
    - item22 후(법인세조정액) — 독립 추정. 그대로.
    - item23 후(기타요구자본) — 현재값이 정확히 old_item14후 − 15후 + 22후 (소수 2자리까지) 로 닫힌다
      = 역산 item14 후에 맞춰 R5 를 닫던 잔차 셀. item14 후가 원문 정수로 바뀌었으니 같은 식으로
      다시 닫는다. (파서 세션이 시도한 "15 후 재파생"은 mmult·R6 두 축을 깼고 되돌렸다:
      scripts/_probes/_revert_20260921_kr0071_15_22_23.py)
  '발행사 불일치 있는 그대로' 원칙(reference_issuer_inconsistent_keep_as_disclosed)은 **공시된** 값을
  파생값으로 갈아끼우지 말라는 것이다. 결합 23 후는 공시된 적이 없는 추정 셀이라 해당 없음.

Guard: asserts current 값_적용후 of items 14/15/22/23 before writing; writes only item23 후 of the 5
buckets; row count invariant.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_Q = "공시분기"
KEY_POST = "값_적용후"

CODE = "KR0071"
# quarter: (item14후 expected, item15후 expected, item22후 expected, item23후 expected_current)
BUCKETS: dict[str, tuple[str, str, str, str]] = {
    "2023.2Q": ("16469", "14615.24", "3342.18", "5198.88"),
    "2023.3Q": ("16456", "14951.43", "3399.98", "4907.07"),
    "2025.2Q": ("18412", "16345.89", "3721.3", "5790.68"),
    "2025.4Q": ("19350", "16941.64", "3868.84", "6281.63"),
    "2026.1Q": ("20995", "18701.22", "4485.45", "6773.61"),
}


def _fmt(x: float) -> str:
    s = f"{round(x, 2):.2f}".rstrip("0").rstrip(".")
    return s


def main() -> int:
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    n_before = len(rows)
    index = {(r[KEY_CODE], r[KEY_Q], r[KEY_ITEM]): r for r in rows}

    plan = []
    for q, (e14, e15, e22, e23) in BUCKETS.items():
        got = {i: index[(CODE, q, i)].get(KEY_POST) for i in (14, 15, 22, 23)}
        exp = {14: e14, 15: e15, 22: e22, 23: e23}
        bad = {i: (exp[i], got[i]) for i in exp if str(got[i]) != exp[i]}
        if bad:
            print(f"ABORT guard mismatch {q}: {bad}")
            return 1
        new23 = float(e14) - float(e15) + float(e22)
        plan.append((q, e23, _fmt(new23)))

    print("guard OK")
    for q, old, new in plan:
        index[(CODE, q, 23)][KEY_POST] = new
        print(f"  {CODE} {q} item23 후: {old} -> {new}  (= item14후 − item15후 + item22후)")

    if len(rows) != n_before:
        print("ABORT row count changed")
        return 1
    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
