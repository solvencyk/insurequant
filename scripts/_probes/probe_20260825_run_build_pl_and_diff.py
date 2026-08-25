# -*- coding: utf-8 -*-
"""build_pl() 만 호출하고 전후 combo-diff. build_root_masters.main() 은 호출하지 않는다
(CSM 은 안 건드림). 결과를 스크래치패드에 저장하고 요약을 인쇄한다.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_run_build_pl_and_diff.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

PL_OUT = ROOT / "PL_breakdown.json"


def index(rows):
    return {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}


def main() -> int:
    before_rows = json.loads(PL_OUT.read_text(encoding="utf-8"))
    before = index(before_rows)
    print(f"BEFORE: {len(before_rows)} rows / {len(before)} keys")

    from scripts.build_root_masters import build_pl
    n = build_pl()
    print(f"build_pl() wrote {n} rows")

    after_rows = json.loads(PL_OUT.read_text(encoding="utf-8"))
    after = index(after_rows)
    print(f"AFTER:  {len(after_rows)} rows / {len(after)} keys")

    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    changed = []
    lost_value = []   # had a non-null value before, None or missing after -- BAD
    for k in before:
        if k not in after:
            continue
        bv = before[k].get("값")
        av = after[k].get("값")
        if bv != av:
            changed.append((k, bv, av))
            if bv is not None and av is None:
                lost_value.append((k, bv, av))

    print(f"\nadded keys:   {len(added)}")
    print(f"removed keys: {len(removed)}")
    print(f"changed 값:   {len(changed)}")
    print(f"LOST (non-null -> None): {len(lost_value)}")

    if removed:
        print("\n-- REMOVED KEYS (first 50) --")
        for k in sorted(removed)[:50]:
            print(" ", k, before[k].get("값"))
    if lost_value:
        print("\n-- LOST VALUE (first 50) --")
        for k, bv, av in lost_value[:50]:
            print(" ", k, bv, "->", av)

    print("\n-- ALL CHANGED CELLS --")
    for k, bv, av in sorted(changed, key=lambda x: (x[0][0], x[0][2], x[0][1])):
        co, item, q = k
        print(f"  {co:20s} item{item:<3d} {q:9s}  {bv!r:>14} -> {av!r:>14}")

    if added:
        print(f"\n-- ADDED KEYS (first 30 of {len(added)}) --")
        for k in sorted(added)[:30]:
            print(" ", k, "=", after[k].get("값"))

    out = ROOT / "scripts" / "_probes" / "_run_build_pl_and_diff_out.json"
    out.write_text(json.dumps({
        "before_rows": len(before_rows), "after_rows": len(after_rows),
        "added": [list(k) for k in added], "removed": [list(k) for k in removed],
        "changed": [[list(k), bv, av] for k, bv, av in changed],
        "lost_value": [[list(k), bv, av] for k, bv, av in lost_value],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
