# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
even_quarters = ["2023.2Q", "2023.4Q", "2024.2Q", "2024.4Q"]
for q in even_quarters:
    items = {r["항목번호"] for r in data if r.get("원보험사코드") == "KR0029" and r.get("공시분기") == q}
    market_present = {i for i in (36,37,38,39,40) if i in items}
    irr_present = {i for i in (41,42,43,44,45,46) if i in items}
    life_present = {i for i in (29,30,31,32,33,34,35) if i in items}
    print(f"{q}: market(36-40)={sorted(market_present)} (missing={sorted(set(range(36,41))-market_present)}) irr(41-46) missing={sorted(set(range(41,47))-irr_present)} life(29-35) missing={sorted(set(range(29,36))-life_present)}")
