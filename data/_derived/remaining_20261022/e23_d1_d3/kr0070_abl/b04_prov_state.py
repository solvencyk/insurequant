# -*- coding: utf-8 -*-
"""read-only: provenance blocks of KR0070 FY2023 (PL_breakdown_provenance.json + CSM_waterfall_provenance.json) as they are now."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
for fn in ("PL_breakdown_provenance.json", "CSM_waterfall_provenance.json"):
    d = json.loads((ROOT / fn).read_text(encoding="utf-8"))
    print("=" * 30, fn, "top keys:", [k for k in d.keys()][:40])
    rows = None
    for k in ("blocks", "rows", "cells", "entries"):
        if k in d and isinstance(d[k], list):
            rows = d[k]
            print("list key", k, len(rows))
            break
    if rows is None:
        print("no list; keys", list(d.keys()))
        continue
    for r in rows:
        if r.get("company_code") == "KR0070" and str(r.get("quarter", "")).startswith(("2023.", "2024.1Q")):
            print(json.dumps(r, ensure_ascii=False)[:1500])
