# -*- coding: utf-8 -*-
"""One-off follow-up of unify_ilp_restated_3cells_2023_4q.py (ticket 20261011T0100Z): in the three provenance cells keep `basis`
= 'liability' (the row-basis meaning validate_insurance_liability_lic.py reads), carry the period basis in `period_basis`, and make
source_file the repo-relative path the validator expects.  Provenance only; the master is untouched."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROV = REPO / "insurance_liability_portfolio_provenance.json"
BASIS = "latest_filing_comparative_restatable"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    txt = PROV.read_text(encoding="utf-8")
    p = json.loads(txt)
    if json.dumps(p, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance does not round-trip")
    n = 0
    for c in p["cells"]:
        if c["company_code"] in ("KR0074", "KR0079", "KR0099") and c["quarter"] == "2023.4Q" and c.get("item_block") == "lic_dart_note" and c.get("basis") == BASIS:
            c["basis"] = "liability"
            c["period_basis"] = BASIS
            if not c["source_file"].startswith("data/"):
                c["source_file"] = "data/dart/FY2024_Q4/raw/" + c["source_file"]
            n += 1
    if n != 3:
        raise SystemExit(f"abort: expected 3 cells, patched {n}")
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes((json.dumps(p, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    os.replace(tmp, PROV)
    print("patched", n)


if __name__ == "__main__":
    main()
