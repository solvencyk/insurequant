"""Read-only probe: Lina (KR0074) ILP (2-4/4-6-2 accounting-model portfolio) tables printed in the FY2024 interim disclosures: do they carry a prior-year-same-quarter table?
Uses the production reader.  usage: python s92_lina_ilp_interim.py [KR0074]"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_insurance_liability_model_pdf as R  # noqa: E402
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

kr = sys.argv[1] if len(sys.argv) > 1 else "KR0074"
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in ilp}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    print("master ILP", kr, q, [M.get((kr, q, i)) for i in range(1, 16)])
for fy in ("FY2023_Q1", "FY2023_Q2", "FY2023_Q3", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"):
    pdfs = latest_disclosure_pdfs(fy, kr)
    if not pdfs:
        print(fy, "no PDF")
        continue
    try:
        sp = R.find_start_page(pdfs[0])
        tabs = R.read_tables(pdfs[0], sp) if sp else None
    except Exception as e:  # noqa: BLE001
        print(fy, "ERR", e)
        continue
    print(fy, pdfs[0].name, "start_page", sp)
    if tabs:
        for t in tabs.get("tables", []):
            print("    year", t.get("year"), "page", t.get("page"), "slots", json.dumps(t.get("slots"), ensure_ascii=False)[:300])
        print("    keys", [k for k in tabs.keys()])
