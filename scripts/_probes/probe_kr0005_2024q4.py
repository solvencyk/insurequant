# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
for r in data:
    if r.get("원보험사코드") != "KR0005":
        continue
    try:
        it = int(r.get("항목번호"))
    except (TypeError, ValueError):
        continue
    if it not in (14, 23):
        continue
    q = r.get("공시분기")
    print(q, f"item{it}", "값=", r.get("값"), "값_적용후=", r.get("값_적용후"))
