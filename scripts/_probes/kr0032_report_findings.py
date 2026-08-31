# -*- coding: utf-8 -*-
"""Filter artifacts/kics_validation/report_latest.json for KR0032 2026.2Q findings, any status."""
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open(r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_latest.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(type(data), list(data.keys()) if isinstance(data, dict) else len(data))

# try common shapes
candidates = []
if isinstance(data, dict):
    for key in ("findings", "results", "records", "rows"):
        if key in data and isinstance(data[key], list):
            candidates = data[key]
            print(f"using key={key}, n={len(candidates)}")
            break
elif isinstance(data, list):
    candidates = data

if not candidates:
    print("Could not find findings list; dumping top-level structure")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
else:
    hits = [r for r in candidates if r.get("원보험사코드") == "KR0032" and r.get("공시분기") == "2026.2Q"]
    print(f"KR0032 2026.2Q findings: {len(hits)}")
    for r in hits:
        print(json.dumps(r, ensure_ascii=False))
