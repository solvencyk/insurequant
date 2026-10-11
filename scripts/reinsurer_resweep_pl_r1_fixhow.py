#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-off provenance fix after `reinsurer_resweep_pl_followup.py --r1`: the 3 NEW cells (KR1103 2023.3Q item 17, KR1105 2023.3Q items 17·20) were listed in the
how=latest_prior_column_R1 entry; they belong under how=disclosure_summary_pl_reinsurer (the key the §3d allowance is meant to read), R1 is for the 11 existing cells.
Sidecar only; moves the items to their own entry (same file / page / printed / column).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_pl_r1_fixhow.py [--apply]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_granularity_load_bs as L  # noqa: E402

SIDECAR = ROOT / "PL_breakdown_provenance.json"
MOVES = {("KR1103", "2023.3Q"): [17], ("KR1105", "2023.3Q"): [17, 20]}


def main():
    side, raw = L.load_json_exact(SIDECAR, 1, "\r\n")
    for b in side["cells"]:
        k = (b["company_code"], b["quarter"])
        if b["item_block"] != "income_statement" or k not in MOVES:
            continue
        r1 = next(e for e in b["source_files"] if e.get("how") == "latest_prior_column_R1")
        items = MOVES[k]
        if not all(i in r1["items"] for i in items):
            raise SystemExit(f"ABORT: {k} items not in the R1 entry")
        new = {"file": r1["file"], "how": "disclosure_summary_pl_reinsurer", "items": list(items), "page": r1["page"],
               "printed": {str(i): r1["printed"].pop(str(i)) for i in items}, "unit": r1["unit"], "column": r1["column"], "later_filing_quarter": r1["later_filing_quarter"]}
        for i in items:
            r1["items"].remove(i)
            r1["replaced_values"].pop(str(i), None)
        b["source_files"].append(new)
        print("fixed", k, "R1 items now", r1["items"], "| new entry", new["items"])
    if "--apply" in sys.argv:
        if SIDECAR.read_bytes() != raw:
            raise SystemExit("ABORT: changed")
        L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
        print("APPLIED")


if __name__ == "__main__":
    main()
