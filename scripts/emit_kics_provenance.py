# -*- coding: utf-8 -*-
"""Phase-2 provenance emission (parser portion) for the kics_disclosure master.

Validation's data-contract gate (CHECK 2) resolves each published metric to a
provenance cell. Per the contract (`validate_data_contract.py --print-provenance-contract`):
sidecar `<master>_provenance.json`, keyed by (company_code, quarter, item_block).
**Routing split**: parser owns `source_id` + `item_block`; downloader fills
`source_file` + `as_of_date` + `effective_filtered` in its own pass.

kics_disclosure.json은 전부 정기경영공시 PDF→docling MD에서 추출 → 전 셀 source_id = DISCLOSURE_MD.
item_block (owner 1242Z 그룹): 1-28 = capital_summary · 29-35 = life_subrisk · 36-46 = market_irr.
"""
import argparse, io, json, sys
from pathlib import Path
from collections import OrderedDict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "kics_disclosure.json"
OUT = REPO / "kics_disclosure_provenance.json"
GENERATED_AT = "20260616T1245Z"  # ISO8601-basic UTC of this emission


def _block(item_no: int) -> str | None:
    if 1 <= item_no <= 28:
        return "capital_summary"
    if 29 <= item_no <= 35:
        return "life_subrisk"
    if 36 <= item_no <= 46:
        return "market_irr"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rows = json.loads(SRC.read_text(encoding="utf-8"))

    # distinct (company_code, quarter, item_block) present in the master
    seen: "OrderedDict[tuple, dict]" = OrderedDict()
    skipped = 0
    for r in rows:
        code = r.get("원보험사코드")
        q = r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            skipped += 1
            continue
        blk = _block(it)
        if not (code and q and blk):
            skipped += 1
            continue
        key = (code, q, blk)
        if key not in seen:
            seen[key] = {
                "company_code": code,
                "quarter": q,
                "item_block": blk,
                "source_id": "DISCLOSURE_MD",
            }

    cells = list(seen.values())
    by_block = {}
    for c in cells:
        by_block[c["item_block"]] = by_block.get(c["item_block"], 0) + 1
    print(f"src rows={len(rows)} skipped={skipped}  cells={len(cells)}")
    print("  by item_block:", dict(by_block))
    print(f"  companies={len({c['company_code'] for c in cells})} "
          f"quarters={len({c['quarter'] for c in cells})}")

    doc = {
        "master": "kics_disclosure",
        "generated_at": GENERATED_AT,
        "emitter": "parser",
        "fields_owned": ["source_id", "item_block"],
        "fields_pending_downloader": ["as_of_date", "source_file", "effective_filtered"],
        "cells": cells,
    }
    if a.dry_run:
        print("(dry-run; no write)")
        print(json.dumps(cells[0], ensure_ascii=False))
        return
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(cells)} cells")


if __name__ == "__main__":
    main()
