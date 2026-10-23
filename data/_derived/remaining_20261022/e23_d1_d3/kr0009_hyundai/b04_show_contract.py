# -*- coding: utf-8 -*-
"""read-only: print apply-contract samples of e23_plan_hd.json"""
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
P = json.loads((Path(__file__).resolve().parent / "e23_plan_hd.json").read_text(encoding="utf-8"))
C = P["apply_contract"]
print({k: (len(v) if isinstance(v, list) else v) for k, v in C.items()})
for e in C["gold_new"]:
    if (e["quarter"], e["item"]) in {("2023.1Q", 1), ("2023.1Q", 2), ("2023.1Q", 4), ("2023.1Q", 13), ("2023.4Q", 4), ("2023.4Q", 17), ("2023.1Q", 19), ("2023.1Q", 32), ("2023.1Q", 15)}:
        print("---", e["code"], e["quarter"], e["item"], "value", e["value"], "was", e["was"])
        print(e["note"])
for e in C["csm_gold_new"][:3] + C["csm_gold_replace"][:4]:
    print("--- CSM", e["code"], e["quarter"], e["item"], "value", e["value"], "was", e["was"])
    print(e["why"])
    if "old_entry" in e:
        print("   old_entry:", json.dumps(e["old_entry"], ensure_ascii=False))
print("seams", [ (s["quarter"], s["item"], s["cls"]) for s in P["seams"] if s["cls"] not in ("consistent",)][:40])
