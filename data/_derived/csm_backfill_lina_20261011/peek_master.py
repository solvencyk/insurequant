# -*- coding: utf-8 -*-
"""Read-only peek: KR0074 rows in CSM_waterfall.json / CSM_amortization.json / CSM_waterfall_provenance.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
print("waterfall rows", len(wf), "keys", list(wf[0].keys()))
rows = [r for r in wf if r["원보험사코드"] == "KR0074"]
print("KR0074 rows", len(rows))
for r in sorted(rows, key=lambda r: (r["공시분기"], r["항목번호"])):
    print(r["공시분기"], r["항목번호"], r["항목명"], r["값"], r.get("값_당분기"), {k: v for k, v in r.items() if k not in ("원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값", "값_당분기")})

am = json.loads((ROOT / "CSM_amortization.json").read_text(encoding="utf-8"))
print("amort rows", len(am), "keys", list(am[0].keys()))
ar = [r for r in am if r["원보험사코드"] == "KR0074"]
print("KR0074 amort rows", len(ar))
for r in sorted(ar, key=lambda r: (r["공시분기"], r["경과차년"])):
    print(r)

pv = json.loads((ROOT / "CSM_waterfall_provenance.json").read_text(encoding="utf-8"))
print("prov keys", list(pv.keys()))
for k, v in pv.items():
    if k != "cells":
        print(k, str(v)[:600])
cells = pv["cells"]
print("prov cells", len(cells))
for c in cells:
    if c.get("company_code") == "KR0074":
        print(c)
print("first 3 cells", cells[:3])
