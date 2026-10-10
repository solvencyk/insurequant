#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage A: extract statement tables from management-disclosure PDFs into per-(company, quarter) JSON.

Output: data/_derived/bspl_granularity_20261011/tables/<KR>_<YYYY.nQ>.json  (raw values, unit not applied)
Run:   C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_scan_tables.py --company KR0050
       ... --company all    (15 unlisted + 8 reinsurer branches)
Reads PDFs only. Writes only into data/_derived/bspl_granularity_20261011/tables/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from _disclosure_pdf_paths import disclosure_pdfs, period_of  # noqa: E402
from bspl_granularity.tables import extract_pdf  # noqa: E402

TIER2 = ["KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR0074", "KR0075", "KR0076", "KR0080",
         "KR0095", "KR0097", "KR0100", "KR1010", "KR1011", "KR1098"]
REINS = ["KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"]
LISTED = ["KR0001", "KR0002", "KR0003", "KR0005", "KR0008", "KR0009", "KR0010", "KR0011", "KR0032", "KR0068",
          "KR0069", "KR0070", "KR0071", "KR0072", "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094",
          "KR0099", "KR0104", "KR0150", "KR1000"]      # DART-sourced companies (2023.1Q/2Q holes etc.)
QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
OUT = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "tables"


def pick_pdf(q: str, code: str):
    pdfs = disclosure_pdfs(period_of(q), code)
    if not pdfs:
        return None
    amended = [p for p in pdfs if "amended" in p.stem]
    return amended[-1] if amended else pdfs[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", required=True)
    ap.add_argument("--quarters", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    codes = (TIER2 + REINS if a.company == "all" else LISTED if a.company == "listed"
             else a.company.split(","))
    qs = a.quarters.split(",") if a.quarters else QUARTERS
    OUT.mkdir(parents=True, exist_ok=True)
    for code in codes:
        for q in qs:
            out = OUT / f"{code}_{q}.json"
            if out.exists() and not a.force:
                continue
            pdf = pick_pdf(q, code)
            if pdf is None:
                continue
            try:
                res = extract_pdf(pdf)
            except Exception as e:  # keep going, record
                res = {"pdf": str(pdf), "error": repr(e), "tables": []}
            res["pdf"] = str(Path(res["pdf"]).relative_to(ROOT)).replace("\\", "/")
            out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
            kinds = [t["kind"] + f"@{t['page']}" for t in res.get("tables", [])]
            print(code, q, res.get("pages"), kinds, flush=True)
        # year-end audit reports kept in raw_aux (reinsurer branches): K-IFRS statements in exact units
        for q in qs:
            if not q.endswith("4Q"):
                continue
            out = OUT / f"{code}_{q}__audit.json"
            if out.exists() and not a.force:
                continue
            aux = sorted((ROOT / "data" / "disclosure" / period_of(q) / "raw_aux").glob(f"{code}_*__audit.pdf"))
            if not aux:
                continue
            try:
                res = extract_pdf(aux[-1])
            except Exception as e:
                res = {"pdf": str(aux[-1]), "error": repr(e), "tables": []}
            res["pdf"] = str(Path(res["pdf"]).relative_to(ROOT)).replace("\\", "/")
            keep = [t for t in res.get("tables", []) if t["kind"] in ("bs_full", "pl_full")]
            for t in keep:
                t["pdf"], t["sha256"] = res["pdf"], res.get("sha256")
            res["tables"] = keep
            out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
            print(code, q, "AUDIT", res.get("pages"), [t["kind"] + f"@{t['page']}" for t in keep], flush=True)


if __name__ == "__main__":
    main()
