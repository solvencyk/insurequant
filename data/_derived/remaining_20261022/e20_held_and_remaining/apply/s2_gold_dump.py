#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 2: read-only dump of the owner gold overlay (data/_gold/user_pl_cells.json) for the target companies -> s2_gold_dump.txt"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/apply/s2_gold_dump.txt"
CODES = ["KR0082", "KR0083", "KR0087", "KR0104", "KR0032", "KR0069", "KR0094", "KR0070", "KR0072", "KR0068", "KR0071"]
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
liveby = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in live}
L = [f"gold top-level keys: {list(gold.keys())}", f"set n={len(gold['set'])}"]
for k in gold:
    if k == "set":
        continue
    v = gold[k]
    L.append(f"  [{k}] type={type(v).__name__} " + (f"keys={list(v.keys())}" if isinstance(v, dict) else f"len={len(v)}"))
by = {}
for e in gold["set"]:
    by.setdefault(e["원보험사코드"], []).append(e)
L.append("gold set entries by company: " + json.dumps({c: len(v) for c, v in sorted(by.items())}, ensure_ascii=False))
for c in CODES:
    es = sorted(by.get(c, []), key=lambda e: (e["공시분기"], e["항목번호"]))
    L.append(f"===== {c}: {len(es)} gold set entries")
    for e in es:
        lv = liveby.get((c, e["항목번호"], e["공시분기"]))
        L.append(f"  {e['공시분기']} i{e['항목번호']:>2} 값={e['값']} was={e.get('was')} live={None if lv is None else lv['값']} keys={[k for k in e.keys() if k not in ('원보험사코드','항목번호','공시분기','값','was','note')]} note={str(e.get('note'))[:240]}")
    for nm in ("null_dangi", "set_dangi"):
        cells = [x for x in gold.get(nm, {}).get("cells", []) if x[0] == c]
        if cells:
            L.append(f"  {nm}: " + json.dumps(cells, ensure_ascii=False)[:1500])
text = "\n".join(L)
OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
