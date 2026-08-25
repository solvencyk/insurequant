# -*- coding: utf-8 -*-
"""불변식 1 감사: 게이트가 검사하는 파일 = 사용자가 보는 파일인가? (read-only)

배경(2026-08-25, validation). `scripts/validate_master_tables.py` L31-32 는

    PL_PATH = "data/dart/viz/pl_breakdown_master.json"   # 파서 중간산출물
    WF_PATH = "CSM_waterfall.json"                       # 배포본

으로, **CSM 축은 배포본을 보는데 PL 축(COVERAGE·PL_BRIDGE·CSM_CROSSCHECK)은 상류 사본**을 본다.
두 파일이 갈라지면 (a) 배포본에만 있는 셀은 이 파일의 PL 검사 3종(COVERAGE·PL_BRIDGE·
CSM_CROSSCHECK)이 순회하지 못하고 (b) 게이트가 내는
HOLE / FAIL 이 아무도 안 보는 파일 얘기가 된다.

이 스크립트는 판단하지 않고 **거리만 잰다**:
  1. 행 수 / 키 집합 차이 (어느 쪽에만 있는 셀이 몇 개인가)
  2. 공유 키의 값 불일치 (배율 큰 순)
  3. 게이트가 찍는 `HOLE-PL (통째)` 버킷이 배포본에도 비었는지 (real vs phantom)

산출은 stdout 만. 파일을 쓰지 않는다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE_PL = ROOT / "data/dart/viz/pl_breakdown_master.json"
DEPLOYED_PL = ROOT / "PL_breakdown.json"

# COVERAGE 가 PL 축에서 쓰는 key_items (validate_master_tables.main 참조)
KEY_ITEMS = ["보험손익", "생명장기 손익", "당기순이익"]


def load(p: Path) -> list:
    return json.loads(p.read_text(encoding="utf-8"))


def key_idx(rows: list) -> dict:
    return {(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")): r for r in rows}


def label_idx(rows: list) -> dict:
    out: dict = {}
    for r in rows:
        out.setdefault((r.get("원수사명"), r.get("공시분기")), {})[r.get("항목명")] = r.get("값")
    return out


def main() -> int:
    src, dep = load(GATE_PL), load(DEPLOYED_PL)
    names = {r["원보험사코드"]: r["원수사명"] for r in dep}
    S, D = key_idx(src), key_idx(dep)

    print("=" * 92)
    print("1. 규모")
    print("=" * 92)
    print(f"  게이트 소스 {GATE_PL.relative_to(ROOT).as_posix()}  rows={len(src):,}  keys={len(S):,}")
    print(f"  배포본     {DEPLOYED_PL.name}                    rows={len(dep):,}  keys={len(D):,}")
    only_s, only_d = set(S) - set(D), set(D) - set(S)
    print(f"  게이트 소스에만 = {len(only_s):,}")
    print(f"  배포본에만     = {len(only_d):,}  <- validate_master_tables 의 PL 검사 3종이 순회 못 하는 셀")
    if only_d:
        c = Counter(k[1] for k in only_d)
        print("     분기별:", ", ".join(f"{q}:{n}" for q, n in sorted(c.items())))
        print("     회사수:", len({k[0] for k in only_d}))

    print()
    print("=" * 92)
    print("2. 공유 키 값 불일치 (상대오차 > 1e-6), 배율 큰 순")
    print("=" * 92)
    diff = []
    for k in set(S) & set(D):
        a, b = S[k].get("값"), D[k].get("값")
        if a is None or b is None:
            continue
        if abs(a - b) > max(1e-6, abs(b) * 1e-6):
            diff.append((abs(a / b) if b else float("inf"), k, a, b))
    diff.sort(key=lambda x: -x[0])
    print(f"  건수={len(diff)}")
    for ratio, k, a, b in diff[:20]:
        print(f"    {names.get(k[0], k[0]):18s} {k[1]} item{k[2]:<4} "
              f"게이트={a!r:>18}  배포본={b!r:>18}  배율={ratio:.6g}")

    print()
    print("=" * 92)
    print("3. 게이트의 `HOLE-PL (통째)` 는 배포본에서도 구멍인가?")
    print("=" * 92)
    SL, DL = label_idx(src), label_idx(dep)
    real = phantom = 0
    for k in sorted(set(SL) | set(DL), key=lambda x: (str(x[0]), str(x[1]))):
        s_empty = all(SL.get(k, {}).get(n) is None for n in KEY_ITEMS)
        d_empty = all(DL.get(k, {}).get(n) is None for n in KEY_ITEMS)
        if not s_empty or k[1].startswith("2023."):
            continue          # 게이트가 hole 로 찍지 않는 버킷
        if d_empty:
            real += 1
        else:
            phantom += 1
            vals = {n: DL[k].get(n) for n in KEY_ITEMS}
            print(f"    PHANTOM {k[0]:16s} {k[1]}  배포본={vals}")
    print(f"\n  real={real}  phantom={phantom}")
    print("\n  (phantom = 게이트 소스에만 없어서 hole 로 보고되지만 사용자가 보는 파일엔 값이 있다)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
