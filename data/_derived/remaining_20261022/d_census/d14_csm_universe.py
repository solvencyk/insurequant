# -*- coding: utf-8 -*-
"""d14: every CSM bucket (2026-10-12 dry-run scan, company x quarter) whose latest comparative column differs from the CURRENT master (not only those in the PL universe)."""
import csv, json, sys
from pathlib import Path
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); D = ROOT / "data/_derived"; OUT = D / "remaining_20261022/d_census"
rows = list(csv.DictReader(open(D / "ifrs17_latest_comparative_precedence_dryrun_20261012/csm_block_verdicts.csv", encoding="utf-8-sig", newline="")))
cs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
CS = defaultdict(dict)
for r in cs: CS[(r["원보험사코드"], r["공시분기"])][int(r["항목번호"])] = r["값"]
uni = {(r["code"], r["q"]) for r in json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8"))}
out = []
for r in rows:
    k = (r["kr"], r["quarter"])
    if r["scan_status"] != "DIFF": continue
    now = [CS[k].get(i) for i in range(1, 7)]
    try: lat = json.loads(r["latest"]); cur = json.loads(r["current"])
    except Exception: continue
    state = "LATEST" if all(abs((a or 0) - (b or 0)) <= 0.051 for a, b in zip(now, lat)) else ("ORIGINAL" if all(abs((a or 0) - (b or 0)) <= 0.051 for a, b in zip(now, cur)) else "NEITHER")
    out.append((r["name"], r["quarter"], r["verdict"], r["fidelity"], r["tier"], state, k in uni, [round(b - a, 1) for a, b in zip(now, lat)]))
print(len(out), "CSM DIFF buckets in the 2026-10-12 scan;", sum(1 for o in out if o[5] == "ORIGINAL"), "still original-vintage in the master;", sum(1 for o in out if o[5] == "ORIGINAL" and not o[6]), "of those not in the PL universe")
for o in sorted(out):
    if o[5] != "LATEST": print(o)
