"""Read-only diagnostic: why did the prior-column reader return nothing for a filing?
For each NO_PRIOR row of csm_prior_scan_v2.csv (optionally filtered by KR code) print: number of blocks, number with extractable stage vectors,
label distribution of those (prior/current/unknown) and the master presence of the quarter.
usage: python s22_diag_no_prior.py [KRxxxx ...]
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import prior_csm as P  # noqa: E402

B = P.B
want = set(sys.argv[1:])
rows = [r for r in csv.DictReader(open(HERE / "csm_prior_scan_v2.csv", encoding="utf-8-sig")) if r["status"] == "NO_PRIOR"]
for r in rows:
    if want and r["kr"] not in want:
        continue
    fy = f"FY{r['later_q'][:4]}_Q{r['later_q'][5]}"
    rd = ROOT / "data/dart" / fy / "raw" / r["dir"]
    name = r["name"]
    blocks = B.blocks_for_dir(rd, name)
    lab = P.label_blocks(blocks)
    with_st = []
    for b, l in lab:
        try:
            st = B.block_stages(b) or B.pattern2_stages(b)
        except Exception:
            st = None
        if st:
            with_st.append((l, b))
    c = Counter(l for l, _ in with_st)
    print(f"{r['kr']} {name[:8]:8s} later={r['later_q']} blocks={len(blocks)} with_stages={len(with_st)} labels={dict(c)} all_labels={dict(Counter(l for _, l in lab))}")
