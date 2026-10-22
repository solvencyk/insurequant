"""g1: owner CSM gold cells (user_csm_cells.json) for chosen company/quarters, next to the master value, the dry-run prior (latest) vector and the original (master) print (READ-ONLY).
usage: g1_csm_gold_view.py KR0070,KR0072,...  [quarters comma list or ALL]"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
codes = sys.argv[1].split(",")
gold = M.jload(M.SNAP / "user_csm_cells.json")
print("keys:", list(gold.keys()))
cs = M.load_csm()
P = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/csm_prior_scan_v2.csv")
with open(P, encoding="utf-8-sig", newline="") as f:
    scan = {(r["kr"], r["prior_q"]): r for r in csv.DictReader(f)}
out = []
for c in gold["set"]:
    if c["원보험사코드"] not in codes:
        continue
    q, it = c["공시분기"], c["항목번호"]
    r = scan.get((c["원보험사코드"], q))
    later = None if not r else (r[f"p{it}"] or None)
    out.append(f"{c['원보험사코드']} {q} item{it}: gold={c.get('값')} | master={cs.get((c['원보험사코드'], q), {}).get(it)} | later-comparative={later} | was={c.get('was')} | note={(c.get('note') or '')[:160]}")
print(len(out), "gold cells")
txt = "\n".join(sorted(out))
M.MEASURE.joinpath("g1_csm_gold_view_" + "_".join(codes) + ".txt").write_text(txt, encoding="utf-8")
print(txt[:9000])
