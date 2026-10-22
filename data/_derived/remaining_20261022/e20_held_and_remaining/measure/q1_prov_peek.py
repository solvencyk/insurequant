"""q1_prov_peek: print provenance blocks of KR0003 2023.1Q/2Q in snapshot vs R2b candidate (READ-ONLY)."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
SCR = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/cand/"
for lab, path in (("SNAP", str(M.SNAP / "PL_breakdown_provenance.json")), ("R2b", SCR + "R2b_Lotte_2023_1Q2Q_PL_breakdown_provenance.json")):
    d = json.loads(open(path, encoding="utf-8").read())
    print("=====", lab, "top keys", [k for k in d if k != "cells"], "ncells", len(d["cells"]))
    for c in d["cells"]:
        if c["company_code"] == "KR0003" and c["quarter"] in ("2023.1Q", "2023.2Q", "2023.3Q"):
            print(c["quarter"], c["item_block"], {k: v for k, v in c.items() if k not in ("company_code", "quarter", "item_block")})
