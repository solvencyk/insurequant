"""Read-only census, ILP domain (insurance_liability_portfolio.json items 1-7 = 회계모형별 BEL/RA/CSM x 일반모형·변동수수료 + PAA): year-end 2024.4Q cell block.

Original  = the master (loaded from the FY2024 결산 disclosure 4-6-2 '<2024년>' table / the DART note).
Latest    = the FY2025 결산 disclosure 4-6-2 '<2024년>' table (the prior-year table printed behind '<2025년>') read with the production reader
            scripts/extract_insurance_liability_model_pdf.py (find_start_page / read_tables).
A block is DIFF when any of the 7 slots differs by more than max(1억, 0.2%) (the print is whole 억원).
Output ilp_yearend_2024_census.csv.  (2023.4Q needs no census: the 4-6-2 section exists only from the FY2024 결산, so the master 2023.4Q is already the latest print.)
"""
from __future__ import annotations

import csv
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
M, NAMES = {}, {}
for r in ilp:
    M[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    NAMES[r["원보험사코드"]] = r.get("원수사명", "")
cos = sorted({k[0] for k in M if k[1] == "2024.4Q" and k[2] == 8})
rows = []
for kr in cos:
    pdfs = latest_disclosure_pdfs("FY2025_Q4", kr)
    row = {"kr": kr, "name": NAMES.get(kr, ""), "quarter": "2024.4Q", "later_filing": "FY2025_Q4 4-6-2 <2024년>"}
    cur = [M.get((kr, "2024.4Q", i)) for i in range(1, 8)]
    row["current"] = json.dumps(cur)
    if not pdfs:
        row.update(status="NO_PDF")
        rows.append(row)
        continue
    try:
        sp = R.find_start_page(pdfs[0])
        tabs = R.read_tables(pdfs[0], sp) if sp else None
    except Exception as e:  # noqa: BLE001
        row.update(status=f"ERR {type(e).__name__}")
        rows.append(row)
        continue
    t24 = None
    for t in (tabs or {}).get("tables", []):
        if t.get("year") == 2024 and t.get("slots"):
            t24 = t
            break
    if not t24:
        row.update(status="NO_PRIOR_TABLE", page=sp)
        rows.append(row)
        continue
    lat = [t24["slots"].get(str(i)) if str(i) in t24["slots"] else t24["slots"].get(i) for i in range(1, 8)]
    row["latest"] = json.dumps(lat)
    row["page"] = t24.get("page")
    bad = []
    for i, (a, b) in enumerate(zip(cur, lat), start=1):
        if a is None or b is None:
            continue
        if abs(a - b) > max(1.0, 0.002 * max(abs(a), abs(b))):
            bad.append(i)
    row["diff_slots"] = ",".join(map(str, bad))
    row["status"] = "DIFF" if bad else "SAME"
    rows.append(row)
    print(kr, row["name"][:8], row["status"], row.get("diff_slots", ""), flush=True)
cols = ["kr", "name", "quarter", "later_filing", "page", "status", "diff_slots", "current", "latest"]
with open(HERE / "ilp_yearend_2024_census.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(Counter(r["status"] for r in rows))
