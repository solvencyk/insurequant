"""Do the reinsurer table-2 pages print a 공동재보험 / 금융재보험 split? (read-only). Also list KR1000 segments in the master."""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[3]
LR = ROOT / "data" / "loss_ratio"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
NEW = [f"KR110{i}" for i in range(1, 8)]
import gzip; src = json.loads(gzip.decompress((LR / "risk_premium_vs_expected_claims.json.gz").read_bytes()).decode("utf-8"))
pages = defaultdict(set)
for r in src:
    if r["원보험사코드"] in NEW:
        pages[r["출처"]["file"]].add(r["출처"]["page"])
KW = re.compile(r"공동\s*재보험|금융\s*재보험|전통형")
lines = []
for f, ps in sorted(pages.items()):
    doc = fitz.open(str(ROOT / f))
    hits = []
    for p in sorted(ps):
        t = re.sub(r"\s+", "", doc[p - 1].get_text("text"))
        if KW.search(t):
            hits.append(p)
    lines.append(f"{f}: table pages {sorted(ps)} -> pages mentioning 공동재보험/금융재보험/전통형: {hits}")
master = json.loads((LR / "master_loss_ratio.json").read_text(encoding="utf-8"))
c = Counter((r["공시분기"], r["세그먼트"]) for r in master if r["원보험사코드"] == "KR1000")
lines.append("KR1000 master segments: " + json.dumps({f"{k[0]}|{k[1]}": v for k, v in sorted(c.items())}, ensure_ascii=False))
(OUT / "scan_cojae.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
