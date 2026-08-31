# -*- coding: utf-8 -*-
"""41건 과거분기 RED 전수 census — 룰별/회사별/분기별 열거."""
import json, sys, collections
from pathlib import Path

ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
rep = json.loads((ROOT / "artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
print("top keys:", list(rep.keys())[:40])

fs = rep.get("findings") or rep.get("results") or []
print("findings n =", len(fs))
if fs:
    print("sample keys:", sorted(fs[0].keys()))

reds = [f for f in fs if f.get("status") == "RED"]
print("RED total =", len(reds))

EXCL = {("KR0029", "2025.2Q"), ("KR0029", "2025.3Q"), ("KR0104", "2026.2Q")}
def key(f):
    return (f.get("원보험사코드") or f.get("code"), f.get("공시분기") or f.get("quarter"))

mine = [f for f in reds if key(f) not in EXCL]
print("mine =", len(mine))
byrule = collections.Counter(f.get("rule") for f in mine)
for r, n in byrule.most_common():
    print(f"  {r:32s} {n}")
out = []
for f in sorted(mine, key=lambda x: (str(x.get("rule")), str(key(x)[0]), str(key(x)[1]))):
    c, q = key(f)
    out.append({"rule": f.get("rule"), "code": c, "name": f.get("원수사명") or f.get("name"),
                "quarter": q, "expected": f.get("expected"), "actual": f.get("actual"),
                "diff": f.get("diff"), "detail": f.get("detail")})
(ROOT / "scripts/_probes/_red41.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote scripts/_probes/_red41.json")
