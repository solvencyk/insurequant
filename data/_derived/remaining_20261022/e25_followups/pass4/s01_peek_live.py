# -*- coding: utf-8 -*-
"""READ-ONLY pass4 s01: dump the LIVE PL master + gold overlay state of KR0032 (NH농협손보) and KR0087 (동양생명) for the cells of ticket 20261024T1000Z.
usage: s01_peek_live.py            -> prints; writes s01_peek_live.txt next to this script"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4"
rows = json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
pins = json.load(open(f"{ROOT}/data/_gold/gold_overlay_ledger.json", encoding="utf-8"))
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
nd = {tuple(x) for x in gold["null_dangi"]["cells"]}
sd = {(x[0], x[1], int(x[2])): x for x in gold["set_dangi"]["cells"]}
out = []


def PR(s=""):
    print(s)
    out.append(s)


def fmt(v):
    return "None" if v is None else f"{v:,.6f}"


PR("top-level keys of user_pl_cells.json: " + ", ".join(gold.keys()))
PR(f"set {len(gold['set'])}  null_dangi {len(gold['null_dangi']['cells'])}  set_dangi {len(gold['set_dangi']['cells'])}  ledger entries {len(pins.get('entries', {}))}")
for code, qs in (("KR0032", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]), ("KR0087", ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"])):
    PR(f"===== {code}")
    for q in qs:
        PR(f"--- {q}")
        for i in range(1, 33):
            r = live.get((code, i, q))
            if r is None:
                continue
            k = (code, i, q)
            tags = []
            if k in gold_by:
                tags.append("GOLD")
            if (code, q, i) in nd:
                tags.append("null_dangi")
            if (code, q, i) in sd:
                tags.append(f"set_dangi={sd[(code, q, i)][3]}")
            pk = f"PL|{code}|{q}|{i}"
            if pk in pins.get("entries", {}):
                tags.append("PINNED")
            PR(f"   {i:>2} {r['항목명'][:14]:14s} 값={fmt(r['값']):>20s}  당분기={fmt(r.get('값_당분기')):>20s}  {','.join(tags)}")
PR("===== gold set entries (full) for the cells of interest")
for code, items, qs in (("KR0032", (1, 16, 17, 18, 19, 20, 21, 22, 23, 24), ["2023.1Q", "2023.2Q", "2023.3Q"]), ("KR0087", (8, 9, 10, 11, 12), ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"])):
    for q in qs:
        for i in items:
            e = gold_by.get((code, i, q))
            if e:
                PR(f"  {code} {q} item {i}: 값={e['값']} was={e.get('was')}\n      note={e.get('note')}")
PR("===== null_dangi cells for these companies: " + str(sorted(x for x in nd if x[0] in ("KR0032", "KR0087"))))
PR("===== set_dangi cells for these companies: " + str(sorted((k, v[3], v[4]) for k, v in sd.items() if k[0] in ("KR0032", "KR0087"))))
PR("doc keys in null_dangi: " + str([k for k in gold["null_dangi"].keys() if k != "cells"]))
open(f"{EV}/s01_peek_live.txt", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
