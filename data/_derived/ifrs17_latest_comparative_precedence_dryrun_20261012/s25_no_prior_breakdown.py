"""Read-only: categorize the NO_PRIOR rows of csm_prior_scan_v2.csv.
  A  master has no CSM block for that quarter (nothing to compare / company has no CSM roll-forward)
  B  master block exists, 0 blocks with stage vectors in the later filing (document has no extractable roll-forward: PAA-only or image/attachment)
  C  master block exists, prior-labelled blocks exist but the picker returned nothing (picker/label gap)
  D  master block exists, stage vectors exist but none labelled prior (marker/caption gap)
"""
from __future__ import annotations

import csv
import json
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
import lib_dryrun as D  # noqa: E402

B = P.B
chain0 = D.csm_chain()
rows = [r for r in csv.DictReader(open(HERE / "csm_prior_scan_v2.csv", encoding="utf-8-sig")) if r["status"] == "NO_PRIOR"]
cat = Counter()
out = []
for r in rows:
    kr, pq = r["kr"], r["prior_q"]
    has_master = pq in chain0.get(kr, {})
    fy = f"FY{r['later_q'][:4]}_Q{r['later_q'][5]}"
    rd = ROOT / "data/dart" / fy / "raw" / r["dir"]
    if not has_master:
        c = "A"
        nvec = npri = nunk = -1
    else:
        blocks = B.blocks_for_dir(rd, r["name"])
        lab = P.label_blocks(blocks)
        nvec = npri = nunk = 0
        for b, l in lab:
            try:
                st = B.block_stages(b) or B.pattern2_stages(b)
            except Exception:
                st = None
            if st:
                nvec += 1
                if l == "prior":
                    npri += 1
                if l == "unknown":
                    nunk += 1
        c = "B" if nvec == 0 else ("C" if npri else "D")
    cat[c] += 1
    out.append((c, r["kr"], r["name"], r["later_q"], r["prior_q"], nvec, npri, nunk))
print(dict(cat))
for c in ("A", "B", "C", "D"):
    print("== category", c)
    by = Counter((o[1], o[2]) for o in out if o[0] == c)
    for (kr, nm), n in sorted(by.items()):
        qs = [o[3] for o in out if o[0] == c and o[1] == kr]
        print(f"   {kr} {nm[:10]:10s} n={n} later={','.join(qs)}")
with open(HERE / "csm_no_prior_categories.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["cat", "kr", "name", "later_q", "prior_q", "n_vec_blocks", "n_prior_labelled", "n_unknown_labelled"])
    w.writerows(out)
