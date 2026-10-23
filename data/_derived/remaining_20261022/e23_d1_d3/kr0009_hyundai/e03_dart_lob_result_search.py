# -*- coding: utf-8 -*-
"""read-only: does the FY2024 Q1 / Q2 DART report print the LOB (장기 / 자동차 / 일반) insurance result for the PRIOR-YEAR period anywhere?  Lists every leaf table whose first rows carry the LOB column headers
(장기, 자동차, 일반) and that has a row labelled 보험손익 / 보험영업손익 / 보험서비스결과 / 손익, with its section title and the nearest period caption, so that the claim 'the later DART filings give no quarterly LOB
breakdown' is evidenced."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hd_lib as H  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
FILES = {"N1": "data/dart/FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml", "N2": "data/dart/FY2024_Q2/raw/KR0009_현대해상/20240814004187.xml"}
RES = re.compile(r"보험손익|보험영업손익|보험서비스결과|영업손익|^손익$")
for key, rel in FILES.items():
    L = H.lines_of(rel)
    ts = H.titles(L)
    tbls = H.all_tables(L)
    print("=" * 100)
    print(key, rel, len(tbls), "leaf tables")
    n_lob = 0
    for (ta, tb) in tbls:
        blob = H.nspace(" ".join(L[ta:min(tb, ta + 80)]))
        if not ("자동차" in blob and "장기" in blob and "일반" in blob):
            continue
        rows = H.table_rows(L, ta, tb)
        hdr_cells = [H.nspace(c["text"]) for r in rows[:3] for c in r["cells"]]
        if not ({"장기", "자동차", "일반"} <= set(hdr_cells)):
            continue
        labs = [H.nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        hit = [x for x in labs if RES.search(x)]
        sec = next((t for (k, t) in reversed(ts) if k < ta), "?")
        cap = None
        for k in range(ta - 1, max(ta - 60, 0), -1):
            t = H.clean(L[k])
            if t and not t.startswith("(단위") and not re.fullmatch(r"[\d,().\-\s]+", t):
                cap = (k + 1, t[:70])
                break
        n_lob += 1
        print(f"  table L{ta + 1}-L{tb + 1} | section {sec[:40]!r} | caption {cap} | rows {len(rows)} | 보험손익-like rows: {hit[:4]} | first labels {labs[:6]}")
    print("  LOB-column tables:", n_lob)
