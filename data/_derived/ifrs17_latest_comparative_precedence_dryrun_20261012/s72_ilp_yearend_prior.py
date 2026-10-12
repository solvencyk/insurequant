"""Read-only probe: ILP 2-4/4-6-2 year-end table - original print vs the latest comparative print (the '<prior year>' table of the NEXT year-end disclosure).
Uses the production reader scripts/extract_insurance_liability_model_pdf.py (find_start_page / read_tables).  Companies given on the command line
(e.g. KR0097 KR0073 KR0099 KR0003); for each year-end Y in 2023, 2024 prints 3+6 (일반모형 CSM + 변동수수료 CSM, 억원) from
  * the year-end Y disclosure (original), * the year-end Y+1 disclosure's '<Y년>' table (latest comparative) and the ILP master value.
"""
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

ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in ilp}
for kr in sys.argv[1:]:
    for y in (2023, 2024):
        print("=" * 100)
        print(kr, f"year-end {y}")
        for src_fy, label in ((f"FY{y}_Q4", "original"), (f"FY{y+1}_Q4", "latest comparative")):
            pdfs = latest_disclosure_pdfs(src_fy, kr)
            if not pdfs:
                print(f"  [{label}] no PDF {src_fy}")
                continue
            pdf = pdfs[0]
            try:
                sp = R.find_start_page(pdf)
                tabs = R.read_tables(pdf, sp) if sp else None
            except Exception as e:  # noqa: BLE001
                print(f"  [{label}] {src_fy}: ERR {e}")
                continue
            print(f"  [{label}] {src_fy} {pdf.name} start_page={sp}")
            if not tabs:
                print("     (no table read)")
                continue
            try:
                print("     ", json.dumps(tabs, ensure_ascii=False, default=str)[:900])
            except Exception:
                print("     ", str(tabs)[:900])
        print("  master ILP items 1-8:", [M.get((kr, f"{y}.4Q", i)) for i in range(1, 9)])
