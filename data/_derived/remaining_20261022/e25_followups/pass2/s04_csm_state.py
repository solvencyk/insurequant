# -*- coding: utf-8 -*-
"""pass2 s04 (read-only): live CSM master (CSM_waterfall.json) items 1..6 (값, 값_당분기, gold?) of a company.
usage: s04_csm_state.py CODE [QUARTERS comma list | all]"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]
qs = None if len(sys.argv) < 3 or sys.argv[2] == "all" else sys.argv[2].split(",")
rows = [r for r in json.load(open(f"{ROOT}/CSM_waterfall.json", encoding="utf-8")) if r["원보험사코드"] == code]
gold = json.load(open(f"{ROOT}/data/_gold/user_csm_cells.json", encoding="utf-8"))
gset = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
nd = {tuple(c) for c in (gold.get("null_dangi") or {}).get("cells", [])}
by = {(r["항목번호"], r["공시분기"]): r for r in rows}
allq = sorted({r["공시분기"] for r in rows})
qs = qs or allq
print(code, rows[0]["원수사명"] if rows else "?")
for it in range(1, 7):
    print(f"--- CSM item {it} {next((r['항목명'] for r in rows if r['항목번호'] == it), '?')}")
    for q in qs:
        r = by.get((it, q))
        if r is None:
            print(f"   {q}: ROW ABSENT"); continue
        g = gset.get((code, it, q))
        tag = ("GOLD " if g else "") + ("null_dangi" if (code, q, it) in nd else "")
        print(f"   {q}: 값 {r['값']!s:>14} 당분기 {r.get('값_당분기')!s:>14} {tag}" + (f" | {g.get('why','')[:90]!r}" if g else ""))
