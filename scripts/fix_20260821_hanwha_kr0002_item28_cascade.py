# -*- coding: utf-8 -*-
"""한화손해(KR0002) 2024.2Q item28(기본자본비율) 값_적용후 -- cascade fix.

`fix_20260821_adversarial_reverification.py` corrected item2후 26377.97 -> 28722.65
(and item3후, item1후) per raw p14 공통적용경과조치표, but item28후 (=item2후/item14후*100)
was a DERIVED field that didn't get recomputed alongside it, so it stayed stale at the
OLD item2후-derived value. The gate's `_transition_ratio_after_capture` AMT_MISMATCH
check caught this immediately on rerun: stored 103.11547633 vs re-derived 112.28 from
the corrected item2후 -- diff 9.17, well outside tolerance.

item14후 = 25581 (unchanged, already correct, matches raw p10 headline 경과조치 후
지급여력기준금액=25,581 -- not touched by the item1/2/3 fix).

item28후 = item2후/item14후*100 = 28722.65/25581*100 = 112.2811852546812.
(item27후="209.3" was independently re-checked against the corrected item1후=53541:
derived 209.29987 vs stored 209.3, diff 0.0001 -- already fine, not touched.)

Usage: ...python scripts/fix_20260821_hanwha_kr0002_item28_cascade.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

GUARD = "103.11547633"
NEW = "112.2811852546812"


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    done = 0
    for r in data:
        if (r.get("원보험사코드") == "KR0002" and r.get("공시분기") == "2024.2Q"
                and int(r.get("항목번호", -1)) == 28):
            cur = r.get("값_적용후")
            if str(cur) != GUARD:
                print(f"SKIP: current={cur!r} != guard {GUARD!r} (already applied?)")
                return 0 if str(cur) == NEW else 1
            print(f"item28[값_적용후]: {cur!r} -> {NEW}")
            if not dry:
                r["값_적용후"] = NEW
            done += 1
    if done != 1:
        print("ABORT: expected exactly 1 match, got", done)
        return 1
    if not dry:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote", TARGET.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
