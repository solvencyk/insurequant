# -*- coding: utf-8 -*-
"""Same census but for the POST column (index 1), to check if any company has a stale
post-column carryforward that the pre-column check would miss. Read-only. 2026-08-22."""
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "data" / "_derived" / "tier2_scale_provenance.json").read_text(encoding="utf-8"))
recs = data["records"]

def qkey(q):
    y, p = q.split(".")
    return (int(y), int(p[0]))

by_code = {}
for r in recs:
    by_code.setdefault(r["원보험사코드"], []).append(r)

hits = []
for code, rs in by_code.items():
    rs = sorted(rs, key=lambda r: qkey(r["공시분기"]))
    for prev, cur in zip(rs, rs[1:]):
        if not prev.get("raw_47") or not cur.get("raw_47"):
            continue
        if not prev.get("raw_48") or not cur.get("raw_48"):
            continue
        if not prev.get("raw_49") or not cur.get("raw_49"):
            continue
        same47 = prev["raw_47"][1] == cur["raw_47"][1]
        same48 = prev["raw_48"][1] == cur["raw_48"][1]
        same49 = prev["raw_49"][1] == cur["raw_49"][1]
        nonzero = abs(cur["raw_47"][1] or 0) > 0.5 or abs(cur["raw_48"][1] or 0) > 0.5
        if same47 and same48 and same49 and nonzero:
            hits.append((code, prev["공시분기"], cur["공시분기"], cur["raw_47"], cur["raw_48"], cur["raw_49"]))

print(f"POST열 연속분기 완전동일(비0) = {len(hits)}건")
for h in hits:
    print(h)
