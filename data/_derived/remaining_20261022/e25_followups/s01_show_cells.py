# -*- coding: utf-8 -*-
"""READ-ONLY: live PL master cells (값, 값_당분기), builder-source cells (pl_breakdown_master.json), PL gold entries and dangi pins for a company and item list.
usage: s01_show_cells.py CODE ITEMS(comma) [QUARTERS(comma)]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]
items = [int(x) for x in sys.argv[2].split(",")]
quarters = sys.argv[3].split(",") if len(sys.argv) > 3 else None

live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == code}
src = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/data/dart/viz/pl_breakdown_master.json", encoding="utf-8")) if r["원보험사코드"] == code}
gold_obj = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold = {(e["공시분기"], e["항목번호"]): e for e in gold_obj["set"] if e["원보험사코드"] == code}
nd = {(x[1], int(x[2])) for x in gold_obj["null_dangi"]["cells"] if x[0] == code}
sd = {(x[1], int(x[2])): x for x in gold_obj["set_dangi"]["cells"] if x[0] == code}
qs = quarters or sorted({q for q, _ in live})
for it in items:
    print(f"--- item {it}")
    for q in qs:
        r = live.get((q, it))
        s = src.get((q, it))
        g = gold.get((q, it))
        print(f"  {q}: live 값={None if r is None else r.get('값')} 당분기={None if r is None else r.get('값_당분기')} | builder-src 값={None if s is None else s.get('값')} 당분기={None if s is None else s.get('값_당분기')}"
              f" | gold={None if g is None else g['값']} was={None if g is None else g.get('was')}"
              f"{' | NULL_DANGI' if (q, it) in nd else ''}{' | SET_DANGI ' + str(sd[(q, it)]) if (q, it) in sd else ''}")
