# -*- coding: utf-8 -*-
"""read-only: ledger pins for KR0009 + builder-source (pl_breakdown_master.json / csm_waterfall_master_diag.json) rows for KR0009 FY2023 + gold entries"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
led = json.loads((ROOT / "data/_gold/gold_overlay_ledger.json").read_text(encoding="utf-8"))
print("ledger keys:", list(led.keys()), "n entries", len(led["entries"]))
for k, v in led["entries"].items():
    if "KR0009" in k:
        print(k, json.dumps(v, ensure_ascii=False)[:600])
src = json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))
srcd = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in src}
print("\nbuilder source PL KR0009 rows by quarter (value):")
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]:
    row = []
    for i in range(1, 33):
        r = srcd.get(("KR0009", i, q))
        row.append(f"{i}:{'ABSENT' if r is None else r['값']}")
    print(q, " ".join(row))
cd = json.loads((ROOT / "data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))
print(type(cd), (list(cd.keys())[:10] if isinstance(cd, dict) else len(cd)))
rows = cd if isinstance(cd, list) else cd.get("rows") or cd.get("cells") or []
cdd = {(r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기")): r for r in rows}
print("\nbuilder source CSM KR0009:")
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]:
    print(q, " ".join(f"{i}:{('ABSENT' if cdd.get(('KR0009', i, q)) is None else cdd[('KR0009', i, q)].get('값'))}" for i in range(1, 7)))
g = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
print("\nPL gold keys:", list(g.keys()))
for e in g["set"]:
    if e["원보험사코드"] == "KR0009":
        print(e["공시분기"], e["항목번호"], e["값"], "was", e.get("was"), "|", str(e.get("note"))[:260].replace("\n", " "))
for k in ("null_dangi", "set_dangi"):
    print(k, json.dumps({kk: vv for kk, vv in g[k].items() if kk != "cells"}, ensure_ascii=False)[:300])
    for c in g[k]["cells"]:
        if c[0] == "KR0009":
            print("   ", c)
cg = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
print("\nCSM gold keys:", list(cg.keys()))
for e in cg["set"]:
    if e["원보험사코드"] == "KR0009":
        print(e["공시분기"], e["항목번호"], e["값"], "was", e.get("was"), "|", json.dumps({k: v for k, v in e.items() if k not in ("원보험사코드", "공시분기", "항목번호", "값", "was")}, ensure_ascii=False)[:900])
