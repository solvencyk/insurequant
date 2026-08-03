# -*- coding: utf-8 -*-
"""Phase-2 provenance emission for sensitivity_heatmap.json — validation inbox
20260721T0530Z__validation__MULTI__sensitivity_heatmap_provenance.md (UH-3 remaining sidecar).

Unlike CSM_waterfall/PL_breakdown (2-phase: parser fills source_id+item_block, downloader fills
as_of_date+source_file), sensitivity_heatmap already carries period/as_of per company (parser
2026-06-16 fix) and its raw dir is resolvable from rcept_no alone (canonical layout
data/dart/FY*_Q*/raw/KR####_<name>_<rcept>/) — so parser emits the COMPLETE sidecar in one pass.

⚠️ Per the gate contract: once this sidecar exists, CHECK 2 flips from Phase-1 inference to
strict Phase-2 (no-sidecar=RED). The gate's `published_cells` for this master only counts
companies with a non-empty `scenarios` list (validate_data_contract.py 2a(i)) — status=
'unavailable' rows (e.g. 엠지손해보험/KR0004, SA=0 미검출) carry no scenarios and are excluded
from that set, so they need no provenance cell. Every company that DOES have scenarios must be
covered here or the gate will RED on MISSING_PROVENANCE for the omitted ones.

⚠️ The gate joins this master's published cells by company NAME, not KR code (the heatmap's own
source rows have no code field) — `company_code` here must hold the exact `company` string from
sensitivity_heatmap.json, and `quarter` must be the SAME derived quarter the gate computes
(`period_label_to_quarter(period, as_of)`, e.g. "2025.4Q"), not the raw "FY2025" period label.
"""
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "dart" / "viz" / "sensitivity_heatmap.json"
OUT = REPO / "data" / "dart" / "viz" / "sensitivity_heatmap_provenance.json"
RAW_ROOT = REPO / "data" / "dart"


def _period_label_to_quarter(period, as_of):
    """Mirrors validate_data_contract.period_label_to_quarter — the gate joins published
    sensitivity_heatmap cells by company NAME + this derived quarter (not the raw 'period'
    label), so the sidecar must use the identical mapping or every cell mismatches."""
    if as_of:
        m = re.match(r"(\d{4})-(\d{2})-\d{2}", as_of)
        if m:
            y, mo = int(m.group(1)), int(m.group(2))
            return f"{y}.{(mo - 1) // 3 + 1}Q"
    if period:
        m = re.match(r"FY(\d{4})", period)
        if m:
            return f"{m.group(1)}.4Q"
    return None


def _find_raw(rcept: str):
    """-> (company_code, source_file_repo_relative) or (None, None) if no raw dir matches."""
    hits = sorted(RAW_ROOT.glob(f"FY*_Q*/raw/*_{rcept}"))
    if not hits:
        return None, None
    d = hits[0]
    code = d.name.split("_", 1)[0]
    # prefer 별도(standalone) body xml, then any {rcept}.xml, then whatever xml exists.
    for cand in (d / f"{rcept}_00760.xml", d / f"{rcept}.xml"):
        if cand.exists():
            return code, str(cand.relative_to(REPO)).replace("\\", "/")
    xmls = sorted(d.glob("*.xml"))
    if xmls:
        return code, str(xmls[0].relative_to(REPO)).replace("\\", "/")
    return code, None


def main():
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    cells, missing = [], []
    for e in doc.get("companies", []):
        if not e.get("scenarios"):
            continue  # gate's published_cells also skips no-scenario rows (nothing rendered)
        name = e.get("company")
        rcept = e.get("rcept_no")
        quarter = _period_label_to_quarter(e.get("period"), e.get("as_of"))
        if not (rcept and quarter):
            missing.append((name, "no rcept/resolvable quarter in source"))
            continue
        code, source_file = _find_raw(rcept)
        if not code:
            missing.append((name, f"no raw dir for rcept {rcept}"))
            continue
        if not source_file:
            missing.append((name, f"raw dir {rcept} has no xml"))
            continue
        cells.append({
            "company_code": name,   # gate joins by NAME for this master, see module docstring
            "kr_code": code,        # auxiliary, not read by the gate — traceability only
            "quarter": quarter,
            "item_block": "sensitivity",
            "source_id": "DART",
            "as_of_date": e.get("as_of"),
            "source_file": source_file,
        })
    out_doc = {
        "master": "sensitivity_heatmap",
        "generated_at": "20260730T0100Z",
        "emitter": "parser",
        "cells": cells,
    }
    OUT.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"sensitivity_heatmap: companies={len(doc.get('companies', []))} cells={len(cells)}")
    print(f"  wrote {OUT.name}")
    if missing:
        print(f"  MISSING ({len(missing)}):")
        for name, why in missing:
            print(f"    {name}: {why}")


if __name__ == "__main__":
    main()
