# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
d = json.loads((ROOT / "data/_derived/kics_transition_applicability.json").read_text(encoding="utf-8"))
print("keys:", list(d.keys()))
recs = d["records"]
print("type(records):", type(recs), "len:", len(recs) if hasattr(recs, "__len__") else "?")
if isinstance(recs, list):
    print("sample[0]:", recs[0])
    aig = [r for r in recs if r.get("원보험사코드") == "KR0029" or r.get("코드") == "KR0029" or "KR0029" in json.dumps(r, ensure_ascii=False)]
    print(f"AIG records: {len(aig)}")
    for r in aig[:20]:
        print(" ", r)
elif isinstance(recs, dict):
    print("KR0029 in records:", "KR0029" in recs)
    if "KR0029" in recs:
        print(json.dumps(recs["KR0029"], ensure_ascii=False, indent=2))
    else:
        print("sample keys:", list(recs.keys())[:10])
print("_meta:", json.dumps(d.get("_meta", {}), ensure_ascii=False, indent=2)[:1000])
