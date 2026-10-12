"""Read-only: which census blocks with an adopt verdict ('최신 채택*') are / are not in plan_final.json, and per-block cell counts (dry-run n_diff vs plan)."""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DR = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"
rows = list(csv.DictReader(open(DR / "census_blocks.csv", encoding="utf-8-sig")))
plan = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
cnt = Counter()
for c in plan["cells"]:
    if c["kind"] == "latest_comparative":
        cnt[(c["master"], c["code"], c["quarter"])] += 1
print("plan latest_comparative blocks:", len(cnt), "cells:", sum(cnt.values()))
used = set()
for r in rows:
    if not r["verdict"].startswith("최신 채택"):
        continue
    key = (r["domain"], r["code"], r["quarter"])
    pk = ("IFRS17_BS" if r["domain"] == "IFRS17_BS" else r["domain"], r["code"], r["quarter"])
    n = cnt.get(pk, 0)
    if n:
        used.add(pk)
    print(f"{'APPLIED' if n else 'NOT   '} {r['domain']:<14} {r['code']} {r['company'][:8]:<9} {r['quarter']} n_diff={r['n_diff']:>3} n_filled={r['n_filled']:>3} plan_cells={n:>3} | {r['verdict']} | gold={r['gold_conflict']} joint={r['joint_group'][:40]}")
print("plan blocks not matched to an adopt census row:", [k for k in cnt if k not in used])
# the dry-run cand/*.json may hold per-block cells; show the dir
print(sorted(p.name for p in (DR / "cand").glob("*"))[:40])
