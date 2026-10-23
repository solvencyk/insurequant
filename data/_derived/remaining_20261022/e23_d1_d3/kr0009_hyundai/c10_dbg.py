# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "e23_plan_hd_final.json").read_text(encoding="utf-8"))
for e in P["apply_contract"]["csm_gold_replace"]:
    print({k: (v if k not in ("why", "old_entry") else "...") for k, v in e.items()})
    print("old why in why:", e["old_entry"]["why"] in e["why"], "| approval:", "owner 2026-10-23 승인" in e["why"])
    print("was", e["was"], "old_entry was", e["old_entry"]["was"])
SIM = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0009_sim")
g = json.loads((SIM / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
for x in g["set"]:
    if x["원보험사코드"] == "KR0009" and x["공시분기"] == "2023.4Q":
        print({k: (v if k != "why" else v[:80]) for k, v in x.items()})
