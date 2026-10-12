"""Read-only peek (NEW-07): all ILP items for KR0074 in 2023.2Q/3Q/4Q + provenance entries."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
rows = [r for r in ilp if r["원보험사코드"] == "KR0074"]
for it in range(1, 18):
    vals = []
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"):
        v = [r["값"] for r in rows if r["항목번호"] == it and r["공시분기"] == q]
        vals.append(f"{q}={v[0] if v else None}")
    nm = next((r["항목명"] for r in rows if r["항목번호"] == it), "")
    print(f"{it:>2} {nm:<28}", " | ".join(vals))
prov = json.loads((ROOT / "insurance_liability_portfolio_provenance.json").read_text(encoding="utf-8"))
print("provenance type:", type(prov).__name__, list(prov.keys())[:10] if isinstance(prov, dict) else len(prov))
txt = json.dumps(prov, ensure_ascii=False)
i = txt.find("KR0074")
print(txt[i - 100:i + 1500])
