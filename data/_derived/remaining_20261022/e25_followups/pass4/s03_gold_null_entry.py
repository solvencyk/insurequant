# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
for e in gold["set"]:
    if e["값"] is None:
        print(json.dumps(e, ensure_ascii=False, indent=1))
rows = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
for r in rows:
    if r["원보험사코드"] == "KR0087" and r["항목번호"] in (8, 9, 10, 11, 12) and r["공시분기"] in ("2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"):
        print(r["공시분기"], r["항목번호"], r["값"], r.get("값_당분기"))
