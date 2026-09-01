# -*- coding: utf-8 -*-
"""Dump full bond-level detail for given company codes from both fy2025 baseline and
fy2026h1 merged output, for manual diagnosis."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
fy25 = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2025.json").read_text(encoding="utf-8"))
h1 = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json").read_text(encoding="utf-8"))

codes = sys.argv[1:] or ["KR0094"]
fy25_by_code = {c["code"]: c for c in fy25["companies"]}
h1_by_code = {c["code"]: c for c in h1["companies"]}

for code in codes:
    print(f"===== {code} =====")
    c25 = fy25_by_code.get(code)
    ch1 = h1_by_code.get(code)
    print(f"--- FY2025 baseline (as_of={c25.get('as_of')}, company={c25.get('company')}) ---")
    for b in c25.get("bonds", []):
        print(f"  [{b['tier']:12s}] {b.get('name')!r} issue={b.get('issue_date')} "
              f"face={b.get('face_amount_mn')} outstanding={b.get('outstanding_mn')} "
              f"call={b.get('call_date')}/{b.get('call_source')}")
    print(f"--- H1 2026 merged (company as_of={ch1.get('as_of')}) ---")
    for b in ch1.get("bonds", []):
        print(f"  [{b['tier']:12s}] {b.get('name')!r} issue={b.get('issue_date')} "
              f"face={b.get('face_amount_mn')} outstanding={b.get('outstanding_mn')} "
              f"as_of={b.get('as_of')} src={b.get('source_file')[:70]!r}")
    print()
