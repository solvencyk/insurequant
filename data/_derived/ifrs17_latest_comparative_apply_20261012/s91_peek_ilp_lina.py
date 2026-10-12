"""Read-only peek: Lina (KR0074) ILP master rows, items 10-15, all quarters (NEW-07 disposition)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
print("ILP rows:", len(ilp), "keys:", list(ilp[0].keys()))
names = {}
for r in ilp:
    names[r["항목번호"]] = r.get("항목명")
print({k: names[k] for k in sorted(names)})
rows = [r for r in ilp if r["원보험사코드"] == "KR0074"]
qs = sorted({r["공시분기"] for r in rows})
print("quarters:", qs)
for it in (10, 11, 12, 13, 14, 15):
    line = []
    for q in qs:
        v = [r for r in rows if r["항목번호"] == it and r["공시분기"] == q]
        line.append(f"{q}={v[0].get('값') if v else None}")
    print(it, names.get(it), " | ".join(line))
