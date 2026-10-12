"""Census of reinsurer (KR1101~KR1107) label combos in the master + the long source (read-only)."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LR = ROOT / "data" / "loss_ratio"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
NEW = [f"KR110{i}" for i in range(1, 8)]

master = json.loads((LR / "master_loss_ratio.json").read_text(encoding="utf-8"))
import gzip
src = json.loads(gzip.decompress((LR / "risk_premium_vs_expected_claims.json.gz").read_bytes()).decode("utf-8"))

lines = []
c = Counter()
for r in master:
    if r["원보험사코드"] in NEW:
        c[(r["원보험사코드"], r["공시분기"], r["세그먼트"], r["구분"], r["상품구분"], r["포트폴리오"], r["원문구분"], r["원문포트폴리오"])] += 1
for k, n in sorted(c.items()):
    lines.append("M\t" + "\t".join(map(str, k)) + f"\t{n}")
s = Counter()
for r in src:
    if r["원보험사코드"] in NEW:
        s[(r["원보험사코드"], r["공시분기"], r["기준연도"], r.get("부문"), r.get("사업구분"), r["구분"], r["포트폴리오"], r.get("포트폴리오_원문"))] += 1
for k, n in sorted(s.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
    lines.append("S\t" + "\t".join(map(str, k)) + f"\t{n}")
(OUT / "census_labels_before.txt").write_text("\n".join(lines), encoding="utf-8")
print(len(c), len(s))
print("master keys", sorted(master[0].keys()))
print("src extra keys", sorted({k for r in src if r["원보험사코드"] in NEW for k in r}))
