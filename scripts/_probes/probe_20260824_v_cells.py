# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
targets = [("KR0097", "2024.4Q"), ("KR0097", "2024.3Q"), ("KR0049", "2024.3Q"),
           ("KR0087", "2025.2Q"), ("KR0087", "2025.4Q"), ("KR0087", "2026.1Q")]
for (c, q) in targets:
    m = {}
    for r in recs:
        if r.get("원보험사코드") == c and r.get("공시분기") == q:
            m[int(r["항목번호"])] = (r.get("값"), r.get("값_적용후"))
    print(f"-- {c} {q}: 항목수 {len(m)}")
    for i in sorted(m):
        print(f"     item{i:<3d} 전={str(m[i][0]):<14s} 후={str(m[i][1]):<14s}")
