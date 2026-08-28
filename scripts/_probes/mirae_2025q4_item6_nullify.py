# -*- coding: utf-8 -*-
"""Coordinator-directed surgical patch (inbox/parser/20260829T1800Z, mid-task course
correction): KR0079(미래에셋생명) 2025.4Q item6(원수 예실차) 0.0 -> None in both
PL_breakdown.json and data/dart/viz/pl_breakdown_master.json.

Rationale (validate_data_contract.py PL_YTD_COLLAPSE_TO_ZERO, RED): item6's YTD series is
+79.2억(2025.2Q) -> △23.5억(2025.3Q) -> 0.0(2025.4Q) -> △71.4억(2026.1Q) -> △181.2억(2026.2Q).
A mid-series exact-0.0 between two populated quarters is the rule's designed signature of "the
rebuild failed to fill this cell", not a real accounting event -- and it flips the derived
값_당분기 for THIS quarter into a physically-wrong sign (+2353.842208 here). This ticket's own
raw-XML investigation (mirae_2025q4_raw_colspan_dump.py / split_vs_unsplit.py) independently
confirmed 2025.4Q genuinely cannot be extracted (label-value shift in the source note's
duplicate rendering) -- so 0.0 here is "could not extract", not "extracted as zero", and the
two are indistinguishable downstream unless we say so with None.

item7 (기타 생명장기 원수손익) is INTENTIONALLY left untouched per coordinator instruction --
it now honestly represents "예실차+기타 결합" for this one quarter, and item3=4+5+6+7 becomes
correctly non-evaluable (not a new defect; the coordinator confirmed this is the intended
result of nullifying item6).

Guards: asserts current 값==0.0 before writing (abort on unexpected pre-state), never touches
item7, and only ever mutates the ONE located record — the rest of each array is passed through
byte-for-byte via json.dumps of the same in-memory list (no rebuild, no full regeneration).
"""
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

DATE = "20260829"
TARGETS = [
    (ROOT / "PL_breakdown.json", True),                          # (path, has_당분기_field)
    (ROOT / "data/dart/viz/pl_breakdown_master.json", False),
]

for path, has_dangi in TARGETS:
    backup = path.with_name(path.name + f".bak_{DATE}_item6_nullify")
    shutil.copy2(path, backup)
    print(f"backup -> {backup}")

    rows = json.loads(path.read_text(encoding="utf-8"))
    hit = [r for r in rows if r.get("원보험사코드") == "KR0079"
           and r.get("공시분기") == "2025.4Q" and r.get("항목번호") == 6]
    assert len(hit) == 1, f"{path.name}: expected exactly 1 item6 row, got {len(hit)} -- ABORT"
    r6 = hit[0]
    assert r6["값"] == 0.0, f"{path.name}: item6 값 not currently 0.0 ({r6['값']!r}) -- ABORT"
    if has_dangi:
        assert r6.get("값_당분기") == 2353.842208, (
            f"{path.name}: item6 값_당분기 unexpected pre-state ({r6.get('값_당분기')!r}) -- ABORT")

    # item7 untouched -- record its pre-state for the post-write diff guard below.
    item7_before = [dict(r) for r in rows
                     if r.get("원보험사코드") == "KR0079" and r.get("공시분기") == "2025.4Q"
                     and r.get("항목번호") == 7]

    r6["값"] = None
    if has_dangi:
        r6["값_당분기"] = None

    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}  ({len(rows)} rows, item6 -> 값=None"
          f"{' 값_당분기=None' if has_dangi else ''})")

    # ---- guard: reread, confirm ONLY item6 changed for this (co,q); item7 byte-identical ----
    reread = json.loads(path.read_text(encoding="utf-8"))
    item7_after = [r for r in reread
                   if r.get("원보험사코드") == "KR0079" and r.get("공시분기") == "2025.4Q"
                   and r.get("항목번호") == 7]
    assert item7_before == item7_after, f"{path.name}: item7 changed unexpectedly -- ABORT/REVIEW"
    diffs = [(i, a, b) for i, (a, b) in enumerate(zip(rows, reread)) if a != b]
    print(f"  guard: item7 unchanged; total rows differing from pre-write in-memory list: "
          f"{len([d for d in diffs])}")
