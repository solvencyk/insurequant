# -*- coding: utf-8 -*-
"""Group1 probe: simulate fill_period_to_disclosure._process for KR0009/KR0010/KR0051
against the REAL master (read-only, never written) to see whether item24/25/26 rows
would get created if the fill script were re-run today, and if so with what value.
Does NOT write kics_disclosure.json.
"""
from __future__ import annotations
import json, io, sys
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from solvency.parser.kics_baseline_match import match_baseline_value_or_zero
from solvency.parser.kics_disclosure_parser import build_label_lookups, extract_kics_detail_rows, normalise_item_value

JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"

rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
F = {"code": "원보험사코드", "cname": "원수사명", "ticker": "티커", "kind": "생손보여부",
     "item": "항목번호", "name": "항목명", "quarter": "공시분기", "val": "값"}

import importlib
mod = importlib.import_module("scripts.fill_period_to_disclosure") if False else None
# reimplement the two helper fns locally (import by path is awkward under scripts/)
sys.path.insert(0, str(REPO / "scripts"))
import fill_period_to_disclosure as FP

TARGET_CODES = {"KR0009", "KR0051"}  # KR0010 handled separately (OCR/gold company)

for code in sorted(TARGET_CODES):
    print(f"\n=========== {code} ===========")
    quarters_for_code = sorted({r[F["quarter"]] for r in rows if r[F["code"]] == code})
    for tq in quarters_for_code:
        period = None
        y, q = tq.split(".")
        qn = q.rstrip("Q")
        period = f"FY{y}_Q{qn}"
        md_dir = MD_INBOX / period
        # find this company's md file in that period dir
        cands = sorted(md_dir.glob(f"{code}_*.md")) if md_dir.is_dir() else []
        if not cands:
            print(f"  {tq}: NO md_inbox file ({period}) - skip")
            continue
        md_path = cands[0]
        bq = FP._quarter_prior(tq)
        baseline = FP._baseline_for_company(rows, code, tq, bq, F)
        have25 = any(str(b.get(F["item"])) == "25" for b in baseline)
        have26 = any(str(b.get(F["item"])) == "26" for b in baseline)
        if not (have25 or have26):
            print(f"  {tq}: item25/26 NOT in supplemented baseline (have25={have25} have26={have26}) - fill would skip both")
            continue
        table = extract_kics_detail_rows(md_path.read_text(encoding="utf-8"), tq)
        if not table:
            print(f"  {tq}: extract_kics_detail_rows returned EMPTY table")
            continue
        lookup, core = build_label_lookups(table)
        results = {}
        for it in (24, 25, 26):
            base = next((b for b in baseline if str(b.get(F["item"])) == str(it)), None)
            if base is None:
                results[it] = "NOT_IN_BASELINE"
                continue
            value = match_baseline_value_or_zero(base[F["name"]], lookup, core, table)
            results[it] = value
        # also show what's actually already in the live master for this (code,tq)
        existing = {int(r[F["item"]]): r[F["val"]] for r in rows if r[F["code"]] == code and r[F["quarter"]] == tq and str(r[F["item"]]).isdigit() and int(r[F["item"]]) in (24,25,26)}
        print(f"  {tq}: sim_match(24,25,26)={results}  existing_master={existing}")
