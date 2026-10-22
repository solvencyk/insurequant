"""s3: DIFF rows of the dry-run CSM prior scan with their chain-check flags (c_open_ok = later filing's current opening equals the prior closing; c_chain_ok) (READ-ONLY)"""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
P = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/csm_prior_scan_v2.csv"
with open(P, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
want = set(sys.argv[1].split(","))
for r in rows:
    if r["kr"] in want and r["status"] in ("DIFF", "SAME", "NO_PRIOR"):
        print(f"{r['kr']} {r['name'][:6]} later={r['later_q']} prior_of={r['prior_q']} {r['status']:<8} fid={r['fidelity']:<5} open_ok={r['c_open_ok']:<5} chain_ok={r['c_chain_ok']:<5} cur_open={r['cur_open']:<9} anchor={r['anchor_p']:<9} nblk={r['n_prior_blocks']:<3} src={r['src'][:26]}")
