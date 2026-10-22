# -*- coding: utf-8 -*-
"""READ-ONLY: fresh build (real build_pl on temp copies, live gold) vs live master vs builder source for KB손보 item 16 / item 1 around 2024.3Q."""
import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_apply as A
sys.stdout.reconfigure(encoding="utf-8")
gold = A.load_json(A.F["GOLD"])
fresh = {A.rkey(r): r for r in A.simulate_rows(gold, "a53")}
live = {A.rkey(r): r for r in A.load_json(A.F["PL"])}
src = {A.rkey(r): r for r in A.load_json(A.PL_MASTER_SRC)}
for q in ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
    for it in (1, 16):
        k = ("KR0010", it, q)
        print(q, "item", it, "| fresh", fresh[k]["값"], "| live", live[k]["값"], "| builder src", src[k]["값"])
