# -*- coding: utf-8 -*-
"""read-only: NB_CSM_multiple rows of KR0072 (is KDB in the NB master at all?)"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
nb = json.loads((ROOT / "NB_CSM_multiple.json").read_text(encoding="utf-8"))
rows = nb if isinstance(nb, list) else nb.get("rows") or nb.get("data") or []
print("type", type(nb).__name__, "n", len(rows) if rows else (list(nb.keys())[:10] if isinstance(nb, dict) else None))
k = [r for r in rows if isinstance(r, dict) and (r.get("원보험사코드") == "KR0072" or "케이디비" in str(r.get("원수사명", "")))]
print("KR0072 rows:", len(k))
for r in k[:12]:
    print({a: r.get(a) for a in list(r)[:12]})
codes = sorted({r.get("원보험사코드") for r in rows if isinstance(r, dict)})
print("companies in NB master:", codes)
