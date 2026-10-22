"""s1: compact view of the 2026-10-12 dry-run CSM prior scan (csm_prior_scan_v2.csv) for chosen companies (READ-ONLY).
usage: s1_csm_scan_view.py KR0099,KR0003,..."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
P = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/csm_prior_scan_v2.csv")
want = set(sys.argv[1].split(","))
with open(P, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
out = []
for r in rows:
    if r["kr"] not in want:
        continue
    def v(prefix):
        return "[" + ", ".join((r[f"{prefix}{i}"] or "-") for i in range(1, 7)) + "]"
    out.append(f"{r['kr']} {r['name'][:7]:<7} later={r['later_q']} prior_of={r['prior_q']} {r['status']:<8} fid={r['fidelity']:<5} diff={r['diff_items']:<12} nblk={r['n_prior_blocks']:<3} src={r['src'][:28]:<28}\n"
               f"      prior(later filing) {v('p')}\n      master(prior_q)     {v('m')}\n      current(later_q)    {v('c')}")
txt = "\n".join(out)
Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/s1_csm_scan_view_" + "_".join(sorted(want)) + ".txt").write_text(txt, encoding="utf-8")
print(txt)
