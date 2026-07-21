# -*- coding: utf-8 -*-
"""Capture owner hand-edits in insurequant_master_tables.xlsx (K-ICS공시 sheet)
into a durable gold layer: data/_gold/user_kics_cells.json.

The xlsx is rebuilt from kics_disclosure.json by build_master_xlsx.py, so any
cell where the xlsx differs from the current JSON (a NEW row, or a changed 값 /
값_적용후) is an owner edit. We persist those so they survive future rebuilds
(generalises the KR0010-only apply_kr0010_gold.py to every company).

Owner uses Excel formulas (=H../H..) for derived ratios — read with
data_only=True to get the cached numeric result. Derived items 27/28 are
EXCLUDED (recalc_kics_derived recomputes them from 1/2/14). Cells the owner
blanked ('-'/''/None) are skipped (no numeric intent).

Output schema:
  { "KR0079": { "2023.4Q": { "2": {"값": 29459, "값_적용후": 30788}, ... } } }
Plus a meta block per company for new-row creation.

Run order (chain): fill_period → fill_market_* → apply_user_kics_gold →
                    apply_kr0010_gold → recalc_kics_derived → validate.
Usage: PYTHONIOENCODING=utf-8 python scripts/build_user_kics_gold.py
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[1]
XLSX = REPO / "insurequant_master_tables.xlsx"
JSON_PATH = REPO / "kics_disclosure.json"
GOLD = REPO / "data" / "_gold" / "user_kics_cells.json"
DERIVED = {27, 28}


def _num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "─", "–", "?"):
        return None
    if s.startswith("="):  # uncomputed formula (data_only gave None)
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _close(a, b) -> bool:
    na, nb = _num(a), _num(b)
    if na is None or nb is None:
        return False
    return abs(na - nb) < 0.01


def _canon(n: float) -> object:
    """int if integral, else rounded float (drop fp noise)."""
    if abs(n - round(n)) < 1e-6:
        return int(round(n))
    return round(n, 6)


def main() -> int:
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb["K-ICS공시"]
    xl = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[0] is not None]
    wb.close()

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    jidx = defaultdict(list)
    for r in rows:
        jidx[(r["원보험사코드"], r["공시분기"], int(r["항목번호"]))].append(r)

    gold: dict = {}
    meta: dict = {}
    names: dict = {}
    n_cells = 0
    for r in xl:
        code, name, tick, kind, item, iname, q, val, post = r
        item = int(item)
        if item in DERIVED:
            continue
        nval = _num(val)
        npost = _num(post)
        if nval is None and npost is None:
            continue
        js = jidx.get((code, q, item))
        jvals = {str(x["값"]) for x in js} if js else set()
        jposts = {str(x.get("값_적용후", "")) for x in js} if js else set()
        cell = {}
        if nval is not None and not any(_close(nval, v) for v in jvals):
            cell["값"] = _canon(nval)
        if npost is not None and not any(_close(npost, p) for p in jposts):
            cell["값_적용후"] = _canon(npost)
        if not cell:
            continue
        gold.setdefault(code, {}).setdefault(q, {})[str(item)] = cell
        names.setdefault(code, {})[str(item)] = iname
        meta.setdefault(code, {"원수사명": name, "티커": tick, "생손보여부": kind})
        n_cells += 1

    out = {"_meta": meta, "_names": names, "cells": gold}
    GOLD.parent.mkdir(parents=True, exist_ok=True)
    GOLD.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    by_co = {c: sum(len(v) for v in qs.values()) for c, qs in gold.items()}
    print(f"user gold built: {n_cells} cells across {len(gold)} companies")
    print(f"  by company: {by_co}")
    print(f"  wrote {GOLD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
