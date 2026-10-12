"""Read-only peek (NEW-07): Lina (KR0074) 17BS items 1,2,3,20 + ILP provenance 2023.x cells."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
rows = [r for r in bs if r["원보험사코드"] == "KR0074"]
qs = ["2022.4Q", "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q"]
for it in (1, 2, 3, 20):
    nm = next((r.get("항목명") for r in rows if r["항목번호"] == it), "")
    vals = []
    for q in qs:
        v = [r["값"] for r in rows if r["항목번호"] == it and r["공시분기"] == q]
        vals.append(f"{q}={v[0] if v else None}")
    print(f"{it:>2} {nm}", " | ".join(vals))
prov = json.loads((ROOT / "insurance_liability_portfolio_provenance.json").read_text(encoding="utf-8"))
for c in prov["cells"]:
    if c.get("company_code") == "KR0074" and c.get("quarter") in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
        print(json.dumps(c, ensure_ascii=False)[:1800])
        print("---")
