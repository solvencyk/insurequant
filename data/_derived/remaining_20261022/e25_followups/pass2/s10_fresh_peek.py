# -*- coding: utf-8 -*-
"""READ-ONLY: run the real build_pl() on a temp copy with the LIVE gold and print the fresh value of the requested cells (code:item:quarter ...)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import p2_apply as A
gold = A.load_json(A.F["GOLD"])
rows = A.simulate_rows(gold, "peek")
by = {A.rkey(r): r for r in rows}
live = {A.rkey(r): r for r in A.load_json(A.F["PL"])}
for spec in sys.argv[1:]:
    c, i, q = spec.split(":")
    k = (c, int(i), q)
    print(spec, "fresh 값", by[k]["값"], "당분기", by[k].get("값_당분기"), "| live 값", live[k]["값"], "당분기", live[k].get("값_당분기"))
