# -*- coding: utf-8 -*-
"""Phase-2 provenance emission (parser portion) for the IFRS17 masters — ifrs17 lane share
of inbox 20260616T1242Z-B / 20260616T1252Z. Mirrors emit_kics_provenance.py.

Per the data-contract provenance contract: sidecar `<master>_provenance.json`, keyed by
(company_code, quarter, item_block). Routing split: parser owns `source_id` + `item_block`;
downloader fills `source_file` + `as_of_date` + `effective_filtered` in its own pass.

CSM_waterfall.json / PL_breakdown.json are all extracted from DART filings → source_id = DART.
item_block (owner contract):
  CSM: csm_waterfall (항목 1-6)
  PL : income_statement (Tier-1 포괄손익계산서 items) · contract_notes (Tier-2 계약유형별/재보험 leg)
Block-level flags: override=true if any member item is an owner manual override (durable
overrides), estimate=true if flagged estimate (현대해상 생명장기 leg — designer 음영)."""
import io
import json
import sys
from collections import OrderedDict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
GENERATED_AT = "20260620T0000Z"

CSM_SRC = REPO / "CSM_waterfall.json"
CSM_OVR = REPO / "data" / "_gold" / "user_csm_cells.json"
CSM_OUT = REPO / "CSM_waterfall_provenance.json"

PL_SRC = REPO / "PL_breakdown.json"
PL_OVR = REPO / "data" / "_gold" / "user_pl_cells.json"
PL_OUT = REPO / "PL_breakdown_provenance.json"

# PL Tier split (build_pl_breakdown): Tier-2 계약유형별/재보험 leg vs everything else (Tier-1 income statement)
PL_CONTRACT_NOTES = {4, 5, 6, 9, 10, 11, 13, 14}


def _load_override_keys(path):
    """-> {(code, item, quarter): {'override': True, 'estimate': bool}}"""
    out = {}
    if not path.exists():
        return out
    obj = json.loads(path.read_text(encoding="utf-8"))
    for s in obj.get("set", []):
        try:
            it = int(s["항목번호"])
        except (TypeError, ValueError, KeyError):
            continue
        out[(s.get("원보험사코드"), it, s.get("공시분기"))] = {
            "override": True, "estimate": bool(s.get("estimate")),
        }
    return out


def _pl_block(it):
    return "contract_notes" if it in PL_CONTRACT_NOTES else "income_statement"


def emit(master_name, src, ovr_path, out, block_fn):
    rows = json.loads(src.read_text(encoding="utf-8"))
    ovr = _load_override_keys(ovr_path)
    seen = OrderedDict()
    skipped = 0
    for r in rows:
        code, q = r.get("원보험사코드"), r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            skipped += 1
            continue
        blk = block_fn(it)
        if not (code and q and blk):
            skipped += 1
            continue
        key = (code, q, blk)
        cell = seen.get(key)
        if cell is None:
            cell = {"company_code": code, "quarter": q, "item_block": blk, "source_id": "DART"}
            seen[key] = cell
        flags = ovr.get((code, it, q))
        if flags:
            if flags["override"]:
                cell["owner_override"] = True
            if flags["estimate"]:
                cell["estimate"] = True
    cells = list(seen.values())
    by_block, n_ovr, n_est = {}, 0, 0
    for c in cells:
        by_block[c["item_block"]] = by_block.get(c["item_block"], 0) + 1
        n_ovr += 1 if c.get("owner_override") else 0
        n_est += 1 if c.get("estimate") else 0
    doc = {
        "master": master_name,
        "generated_at": GENERATED_AT,
        "emitter": "parser",
        "fields_owned": ["source_id", "item_block"],
        "fields_pending_downloader": ["as_of_date", "source_file", "effective_filtered"],
        "cells": cells,
    }
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{master_name}: rows={len(rows)} skipped={skipped} cells={len(cells)} "
          f"blocks={dict(by_block)} owner_override={n_ovr} estimate={n_est}")
    print(f"  wrote {out.name}")


emit("CSM_waterfall", CSM_SRC, CSM_OVR, CSM_OUT, lambda it: "csm_waterfall" if 1 <= it <= 6 else None)
emit("PL_breakdown", PL_SRC, PL_OVR, PL_OUT, _pl_block)
