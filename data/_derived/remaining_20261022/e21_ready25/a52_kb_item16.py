# -*- coding: utf-8 -*-
"""READ-ONLY: KB손보 KR0010 item 16 across quarters: HEAD master, live master, builder source, gold, plan entry."""
import json, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
def head(rel):
    return json.loads(subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout.decode("utf-8"))
hm = {(r["공시분기"], r["항목번호"]): r for r in head("PL_breakdown.json") if r["원보험사코드"] == "KR0010"}
lm = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0010"}
sm = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/data/dart/viz/pl_breakdown_master.json", encoding="utf-8")) if r["원보험사코드"] == "KR0010"}
gold = {(e["공시분기"], e["항목번호"]): e for e in json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))["set"] if e["원보험사코드"] == "KR0010"}
plan = json.load(open("e21_plan.json", encoding="utf-8"))
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"):
    k = (q, 16)
    print(q, "HEAD", hm.get(k, {}).get("값"), "| live", lm.get(k, {}).get("값"), "dangi", lm.get(k, {}).get("값_당분기"), "| builder src", sm.get(k, {}).get("값"), "| gold", gold.get(k, {}).get("값"))
for b in plan["buckets"]:
    if b["code"] == "KR0010" and b["quarter"] == "2024.3Q":
        for c in b["cells"]:
            if c["item"] == 16:
                print("plan cell:", {f: c[f] for f in c if f in ("item", "old", "new", "value", "cls", "gold_src")})
