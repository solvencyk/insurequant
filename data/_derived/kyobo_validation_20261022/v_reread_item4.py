# -*- coding: utf-8 -*-
"""PL item 4 (원수 CSM상각 = '(3) 당기손익에 인식한 보험계약마진 금액' of the 보험수익 note, separate FS) re-read
from the latest filing that prints the period as comparative; compare with PL_breakdown.json item 4."""
import sys, json, re
sys.path.insert(0, "data/_derived/kyobo_validation_20261022")
from vreader import *
from vfiles import main_xml
PLAN = {"2023.1Q": "FY2024_Q1", "2023.2Q": "FY2024_Q2", "2023.3Q": "FY2024_Q3", "2023.4Q": "FY2024_Q4",
        "2024.1Q": "FY2025_Q1", "2024.2Q": "FY2025_Q2", "2024.3Q": "FY2025_Q3", "2024.4Q": "FY2025_Q4"}
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
M = {(r["공시분기"], int(r["항목번호"])): r["값"] for r in pl if r["원수사명"] == "교보생명보험"}
bad = 0
for q, fy in PLAN.items():
    f = main_xml(fy); T = read_tables(f)
    hits = []
    for t in T:
        if "5.재무제표주석" not in t["title"].replace(" ", ""): continue
        hdr = " ".join(c for r in t["rows"][:3] for c in r["cells"])
        for k, r in enumerate(t["rows"]):
            if r["cells"] and re.sub(r"\s", "", r["cells"][0]).startswith("(3)당기손익에인식한보험계약마진금액"):
                tot = [x for x in t["rows"] if x["cells"] and x["cells"][0].replace(" ", "") == "합계"]
                hits.append((t["line"], r["line"], r["cells"][1:], hdr[:80], tot[0]["cells"][1:] if tot else None))
    print(f"== {q} {f}")
    for h in hits: print("   table@%s row@%s vals=%s hdr=%s total=%s" % h)
    annual = q.endswith("4Q")
    if not hits: print("   NO HIT"); bad += 1; continue
    vals = [num(c) for c in hits[0][2]]
    idx = (len(vals) - 1)               # last column = prior-period YTD (2 cols: 당/전; 4 cols: 3M/누적/3M/누적)
    v = vals[idx]
    m = M.get((q, 4))
    ok = m is not None and v is not None and abs(v - m) < 0.5
    bad += (not ok)
    print(f"   item4 raw(prior YTD col)={v} master={m} {'OK' if ok else 'MISMATCH'}")
print("mismatches/no-hit:", bad)
