# -*- coding: utf-8 -*-
"""Read-only full census: does the same raw_47/48/49 pre-triple recur identically in the
immediately-following quarter's tier2_scale_provenance record, for ANY company (not just
KR0003)? This is independent of the loaded master (uses provenance raw_* fields directly,
which come straight off each quarter's own PDF extraction). 2026-08-22 investigation."""
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
        same47 = prev["raw_47"][0] == cur["raw_47"][0]
        same48 = prev["raw_48"][0] == cur["raw_48"][0]
        same49 = prev["raw_49"][0] == cur["raw_49"][0]
        if same47 and same48 and same49:
            m14_prev, m14_cur = prev.get("m14_pre"), cur.get("m14_pre")
            scr_changed = (m14_prev is not None and m14_cur is not None
                           and abs(m14_prev - m14_cur) > 0.5)
            hits.append((code, prev["공시분기"], cur["공시분기"], scr_changed, m14_prev, m14_cur,
                         cur["raw_47"], cur["raw_48"], cur["raw_49"]))

print(f"전수: {sum(len(v) for v in by_code.values())}건 중 연속분기 raw47/48/49(pre) 완전동일 = {len(hits)}건")
for h in hits:
    print(h)
