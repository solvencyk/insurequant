"""Per reinsurer filing: pages / year / segment fields of the long source rows (read-only)."""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LR = ROOT / "data" / "loss_ratio"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
NEW = [f"KR110{i}" for i in range(1, 8)]
import gzip
src = json.loads(gzip.decompress((LR / "risk_premium_vs_expected_claims.json.gz").read_bytes()).decode("utf-8"))
d = defaultdict(lambda: defaultdict(set))
for r in src:
    if r["원보험사코드"] in NEW:
        k = (r["원보험사코드"], r["출처"]["file"].split("/")[-3] if False else r["출처"]["file"])
        d[k][(r["공시분기"], r["기준연도"], r.get("부문") or "", r.get("사업구분") or "")].add(r["출처"]["page"])
lines = []
for k in sorted(d):
    lines.append(k[0] + "  " + k[1])
    for kk, pages in sorted(d[k].items()):
        lines.append(f"    q={kk[0]} yr={kk[1]} 부문={kk[2]!r} 사업구분={kk[3]!r} pages={sorted(pages)}")
(OUT / "census_sources.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
