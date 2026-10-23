# -*- coding: utf-8 -*-
"""pass2 s01 (read-only): live state of the PL items 1..12 / 16..32 (值, 값_당분기, gold?) for the companies and quarters of ticket 20261024T0300Z.
usage: s01_live_state.py CODE [ITEMS comma list or 'all'] [QUARTERS comma list or 'all']"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
code = sys.argv[1]
items = None if len(sys.argv) < 3 or sys.argv[2] == "all" else [int(x) for x in sys.argv[2].split(",")]
qs = None if len(sys.argv) < 4 or sys.argv[3] == "all" else sys.argv[3].split(",")
rows = [r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == code]
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gset = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
nd = {tuple(c) for c in gold["null_dangi"]["cells"]}
sd = {(c[0], c[1], int(c[2])): c for c in gold["set_dangi"]["cells"]}
by = {(r["항목번호"], r["공시분기"]): r for r in rows}
allq = sorted({r["공시분기"] for r in rows})
allit = sorted({r["항목번호"] for r in rows if isinstance(r["항목번호"], int)})
qs = qs or allq
items = items or allit
print(code, rows[0]["원수사명"] if rows else "?", "quarters", qs)
for it in items:
    print(f"--- item {it} {next((r['항목명'] for r in rows if r['항목번호'] == it), '?')}")
    for q in qs:
        r = by.get((it, q))
        if r is None:
            print(f"   {q}: ROW ABSENT")
            continue
        g = gset.get((code, it, q))
        tag = []
        if g is not None:
            tag.append("GOLD")
        if (code, q, it) in nd:
            tag.append("null_dangi")
        if (code, q, it) in sd:
            tag.append(f"set_dangi={sd[(code, q, it)][3]}")
        print(f"   {q}: 값 {r['값']!s:>20} 당분기 {r.get('값_당분기')!s:>20}  {' '.join(tag)}" + (f"  | gold note: {g['note'][:110]!r}" if g is not None else ""))
