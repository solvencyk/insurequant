# -*- coding: utf-8 -*-
"""PL 커버리지 매니페스트 **자신의 변이시험** — 선언을 흔들면 테스트가 실제로 죽는가.

매니페스트가 통과하는 것만으로는 부족하다. 그 테스트가 **어떤 경우에도 통과하는 자동통과**
라면 선언은 면제와 구별되지 않는다(이 저장소가 `48_tier2_limit` 에서 한 번 본 형태).

3가지를 흔든다:
  1. item6(BLIND) 을 GUARDED 로 선언 -> 무방비이므로 실패해야 한다
  2. item22(GUARDED) 를 BLIND 로 선언 -> 2f 가 잡으므로 실패해야 한다
  3. 게이트의 PL_ITEMS_UNCHECKABLE_BY_EQUATION 에서 한 항목을 지움 -> 정합성 검사가 죽어야 한다
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

import test_rule_coverage_manifest as M  # noqa: E402
import validate_master_tables as V       # noqa: E402


def baseline():
    rows = M._pl_rows()
    wf = V.load_long(V.WF_PATH)
    el, uh = V.load_pl_extra_lob(V.PL_PATH)
    return rows, wf, el, uh, M._pl_blocking_signature(rows, wf, el, uh)


def check(base, item, label):
    try:
        M.test_pl_constructive_coverage_matches_manifest(base, item)
    except AssertionError as e:
        print(f"  OK   {label}: 죽었다 — {str(e).splitlines()[0][:110]}")
        return True
    print(f"  BAD  {label}: 그대로 통과했다 (자동통과 = 선언이 면제와 같다)")
    return False


def main():
    base = baseline()
    print("baseline 지문:", {k: len(v) for k, v in base[4].items()})
    ok = True

    print("\n[1] item6 을 GUARDED 로 오선언")
    why6 = M.PL_CONSTRUCTIVE_BLIND.pop(6)
    M.PL_CONSTRUCTIVE_GUARDED[6] = "(변이시험) 잡힌다고 거짓 선언"
    ok &= check(base, 6, "item6 GUARDED 오선언")
    M.PL_CONSTRUCTIVE_GUARDED.pop(6)
    M.PL_CONSTRUCTIVE_BLIND[6] = why6

    print("\n[2] item22 를 BLIND 로 오선언")
    why22 = M.PL_CONSTRUCTIVE_GUARDED.pop(22)
    M.PL_CONSTRUCTIVE_BLIND[22] = "(변이시험) 무검사라고 거짓 선언"
    ok &= check(base, 22, "item22 BLIND 오선언")
    M.PL_CONSTRUCTIVE_BLIND.pop(22)
    M.PL_CONSTRUCTIVE_GUARDED[22] = why22

    print("\n[3] 게이트 인쇄목록에서 item19 삭제")
    keep = V.PL_ITEMS_UNCHECKABLE_BY_EQUATION.pop(19)
    try:
        M.test_pl_blind_items_are_declared_in_the_gate()
        print("  BAD  정합성 검사가 그대로 통과했다")
        ok = False
    except AssertionError as e:
        print(f"  OK   죽었다 — {str(e).splitlines()[0][:110]}")
    V.PL_ITEMS_UNCHECKABLE_BY_EQUATION[19] = keep

    print("\n[4] 정상 상태 재확인 (전 항목)")
    bad = []
    for it in sorted(set(M.PL_CONSTRUCTIVE_BLIND) | set(M.PL_CONSTRUCTIVE_GUARDED)):
        try:
            M.test_pl_constructive_coverage_matches_manifest(base, it)
        except AssertionError as e:
            bad.append((it, str(e).splitlines()[0][:80]))
    print(f"  실패 {len(bad)}건 {bad}")
    ok &= not bad
    print(f"\n결과: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
