# -*- coding: utf-8 -*-
import csv, sys, json, ast
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); D = ROOT / "data/_derived"; OUT = D / "remaining_20261022/d_census"
def rd(p): return list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))
pv = {(r["kr"], r["quarter"]): r for r in rd(D/"ifrs17_latest_comparative_precedence_dryrun_20261012/pl_block_verdicts.csv")}
cv = {(r["kr"], r["quarter"]): r for r in rd(D/"ifrs17_latest_comparative_precedence_dryrun_20261012/csm_block_verdicts.csv")}
cb = {(r["code"], r["quarter"], r["domain"]): r for r in rd(D/"ifrs17_latest_comparative_precedence_dryrun_20261012/census_blocks.csv")}
held = defaultdict(list)
for r in rd(D/"ifrs17_latest_comparative_apply_20261012/held_blocks.csv"):
    held[(r["code"], r["quarter"], r["master"])].append(r)
cs = json.loads((ROOT/"CSM_waterfall.json").read_text(encoding="utf-8"))
CS = defaultdict(dict)
for r in cs: CS[(r["원보험사코드"], r["공시분기"])][int(r["항목번호"])] = (r["값"], r["값_당분기"])
res = json.loads((OUT/"d1_scan.json").read_text(encoding="utf-8"))
def differs(a, b, floor, rel=0.001): return a is not None and b is not None and abs(a - b) > max(rel * abs(a), floor)
sel = []
for r in res:
    if r["code"] == "KR0073": continue
    d = {k: v for k, v in r["items"].items() if k in ("1", "22", "23", "24") and differs(v["same"], v["prior"], 200)}
    if d: sel.append(r)
print(len(sel))
for r in sel:
    k = (r["code"], r["q"])
    p = pv.get(k); c = cv.get(k)
    print(f"== {r['name']} {r['q']} | PL10-12: {(p or {}).get('verdict')} real={(p or {}).get('real_items')} signflip={(p or {}).get('sign_flip_items')} latest={(p or {}).get('already_latest_items')} gold={(p or {}).get('gold_cells')} ")
    if c:
        cur = CS[k]; now = [cur.get(i, (None,))[0] for i in range(1, 7)]
        print(f"      CSM10-12: {c['verdict']} status={c['scan_status']} fid={c['fidelity']} tier={c['tier']} diff={c['diff_items']} current={c['current']} latest={c['latest']} | master now={now}")
    else:
        print("      CSM10-12: (no row)")
    for dom in ("PL_breakdown", "CSM_waterfall"):
        h = held.get((r["code"], r["q"], dom))
        if h: print("      HELD", dom, [(x['decision'], x['reason'][:140]) for x in h])
