# -*- coding: utf-8 -*-
"""READ-ONLY lead for the orchestrator: the 2026-10-11 granularity load round 1 wrote item 16 (기타사업비용) cells from the 경영공시 요약 PL (억원-rounded) into cells the build leaves blank.
For every item-16 cell it added, compare the CURRENT live master value with the builder-source (DART) value of the same cell: a large ratio = different concept / wrong cell (as for KB손보 2024.4Q / 2025.2Q)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant"
man = json.load(open(f"{R}/data/_derived/bspl_granularity_20261011/load_manifest_pl.json", encoding="utf-8"))
added = []
for rd in man["rounds"]:
    added += [x for x in rd.get("added", []) if x.split("|")[1] == "16"]
reverted = set()
for rv in man.get("reverted", []) if isinstance(man.get("reverted"), list) else []:
    reverted.add(rv if isinstance(rv, str) else json.dumps(rv))
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{R}/PL_breakdown.json", encoding="utf-8"))}
src = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{R}/data/dart/viz/pl_breakdown_master.json", encoding="utf-8"))}
gold = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in json.load(open(f"{R}/data/_gold/user_pl_cells.json", encoding="utf-8"))["set"]}
print(f"round-1 item-16 cells added: {len(added)}")
n_diff = 0
for x in added:
    c, i, q = x.split("|")
    k = (c, 16, q)
    lv, sv = live.get(k, {}).get("값"), src.get(k, {}).get("값")
    flag = ""
    if lv is not None and sv not in (None, 0) and abs(lv - sv) > 0.02 * abs(sv):
        flag = "  <== live != builder source (ratio %.2f)" % (lv / sv)
        n_diff += 1
    print(f"  {c} {q}: live {lv} | builder source {sv}{' | gold' if k in gold else ''}{flag}")
print("cells whose live value differs >2% from the DART builder source:", n_diff)
