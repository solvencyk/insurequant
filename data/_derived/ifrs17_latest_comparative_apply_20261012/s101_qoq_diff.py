"""Read-only: compute the gate's QOQ_DELTA_WARN rows (validate_master_tables.qoq_scan) for the LIVE CSM master and for a candidate CSM master and print the set difference.
usage: s101_qoq_diff.py <candidate CSM_waterfall.json>
The gate's own writer is NOT called (only qoq_scan / load_long)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
import validate_master_tables as V  # noqa: E402

CSM_QOQ = [("신계약CSM", "new_business_csm", True), ("이자부리", "csm_interest_accretion", True),
           ("CSM상각", "csm_amortization", True), ("기말CSM", "csm_closing", False)]


def rows_for(path):
    old = V.WF_PATH
    V.WF_PATH = Path(path)
    try:
        wf = V.load_long(V.WF_PATH)
    finally:
        V.WF_PATH = old
    cfg = V.load_qoq_cfg()
    rows = V.qoq_scan(wf, CSM_QOQ, 50.0, cfg)
    return {(c, q, it): (round(d * 100, 1), round(a, 1), round(b, 1), bs) for c, q, it, d, t, a, b, bs in rows}


live = rows_for(ROOT / "CSM_waterfall.json")
cand = rows_for(sys.argv[1])
print("live", len(live), "candidate", len(cand))
for k in sorted(set(live) - set(cand)):
    print("GONE ", k, live[k])
for k in sorted(set(cand) - set(live)):
    print("NEW  ", k, cand[k])
for k in sorted(set(cand) & set(live)):
    if cand[k] != live[k]:
        print("CHG  ", k, live[k], "->", cand[k])
