# -*- coding: utf-8 -*-
"""Read-only: compare pre-patch vs post-patch tfi_capital_memo_rows_provenance.json
scale/scale_method per bucket, and list every bucket whose scale_method changed."""
from __future__ import annotations
import json, sys, os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)
REPO = Path(__file__).resolve().parents[2]
OLD = Path(r"C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/c9c7c053-f96a-4878-bcb0-5ff8567de9fd/scratchpad/tfi_capital_memo_rows_provenance.PREPATCH.json")
NEW = REPO / "data" / "_derived" / "tfi_capital_memo_rows_provenance.json"

old = json.loads(OLD.read_text(encoding="utf-8"))
new = json.loads(NEW.read_text(encoding="utf-8"))


def index(recs):
    return {(r["원보험사코드"], r["공시분기"]): r for r in recs}


oi, ni = index(old["records"]), index(new["records"])
keys = sorted(set(oi) | set(ni))
changed = []
for k in keys:
    o, n = oi.get(k), ni.get(k)
    o_sm = o["scale_method"] if o else None
    n_sm = n["scale_method"] if n else None
    o_sc = o["scale"] if o else None
    n_sc = n["scale"] if n else None
    if o_sm != n_sm or o_sc != n_sc:
        changed.append((k, o_sc, o_sm, n_sc, n_sm))

print(f"총 버킷: old={len(oi)} new={len(ni)} | scale/scale_method 변경 버킷 = {len(changed)}")
for (c, q), o_sc, o_sm, n_sc, n_sm in changed:
    print(f"  {c} {q}: scale {o_sc}({o_sm}) -> {n_sc}({n_sm})")
