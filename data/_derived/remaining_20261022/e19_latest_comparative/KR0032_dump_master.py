# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
L = []
L.append("gold top keys: " + str(list(gold.keys())))
for k, v in gold.items():
    if isinstance(v, dict):
        L.append(f"  {k}: dict keys={list(v.keys())[:8]}")
    elif isinstance(v, list):
        L.append(f"  {k}: list len={len(v)}")
kr = [r for r in rows if r["원보험사코드"] == "KR0032"]
L.append(f"KR0032 rows {len(kr)}; row keys {list(kr[0].keys())}")
names = {}
for r in kr:
    names[r["항목번호"]] = r.get("항목명") or r.get("항목")
L.append("names " + json.dumps(names, ensure_ascii=False))
qs = ["2023.1Q","2023.2Q","2023.3Q","2023.4Q","2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q"]
by = {(r["항목번호"], r["공시분기"]): r for r in kr}
for i in sorted(names):
    for q in qs:
        r = by.get((i, q))
        if r is None: 
            L.append(f"i{i} {q} MISSING"); continue
        L.append(f"i{i} {q} 값={r['값']} 당분기={r.get('값_당분기')} " + " ".join(f"{k}={r[k]}" for k in r if k not in ('원보험사코드','항목번호','공시분기','값','값_당분기','항목명','원보험사명') and r[k] not in (None,""))[:200])
g = [e for e in gold["set"] if e["원보험사코드"] == "KR0032"]
L.append(f"GOLD set KR0032: {len(g)}")
for e in g: L.append("G " + json.dumps(e, ensure_ascii=False)[:400])
for k in ("null_dangi","set_dangi"):
    if k in gold:
        c = [x for x in gold[k].get("cells", []) if x[0] == "KR0032"]
        L.append(f"{k} KR0032 {c}")
(OUT / "KR0032_master_dump.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
