#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provenance page fix (2026-10-11, parser/ifrs17).

The BS loader recorded `page` = the FIRST page of the multi-page statement table; the printed number of some cells sits on a later
page of the same table (KR1101 liabilities on p22 while the table starts on p16).  A scan of every loaded cell against the PDF text
(scratchpad verify_provenance2.py -> data/_derived/bspl_granularity_20261011/provenance_scan_20261011.json, `other_page`) found the
true page for 127 cells.  This script rewrites ONLY `page` and the `p<N>` token of the 근거 text of those cells (this ticket's own new
keys) in the part files, the sidecar and the overlay.  Values/keys/order/other fields are untouched; byte-exact round trip is
verified first, the files are re-read right before the write, backups go to .../backup_20261011/round_pagefix/.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_fix_pages.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import bspl_granularity_load_bs as L  # noqa: E402

SCAN = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "provenance_scan_20261011.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    fixes = {}
    for k, old, where, _composite in scan["other_page"]:
        later = [p for p in where if p >= old]
        fixes[k] = (old, min(later) if later else where[0])

    ov, raw_ov = L.load_json_exact(L.OVERRIDES, 2, "\n")
    sd, raw_sd = L.load_json_exact(L.SIDECAR, 2, "\r\n")
    parts, raw_parts = {}, {}
    for f in sorted(glob.glob(str(L.PARTS / "*_agent_gran.json"))):
        p = Path(f)
        raw = p.read_bytes()
        obj = json.loads(raw.decode("utf-8"))
        if json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8") != raw:
            raise SystemExit(f"ABORT: {p.name} does not round-trip byte-exactly")
        parts[p.stem.split("_")[0]] = (p, obj)
        raw_parts[p] = raw

    changed = []
    for code, (p, obj) in parts.items():
        for k, cell in obj["cells"].items():
            if k not in fixes:
                continue
            old, new = fixes[k]
            if int(cell.get("page") or -1) != old:
                raise SystemExit(f"ABORT: {k} page {cell.get('page')} != scanned {old}")
            if old == new:
                continue
            tok = re.compile(rf"\bp{old}\b")
            if len(tok.findall(cell["근거"])) != 1:
                raise SystemExit(f"ABORT: {k} 근거 has {len(tok.findall(cell['근거']))} 'p{old}' tokens")
            old_txt = cell["근거"]
            new_txt = tok.sub(f"p{new}", old_txt, count=1)
            cell["page"] = new
            cell["근거"] = new_txt
            for tgt, name in ((ov["cells"], "overlay"), (sd["cells"], "sidecar")):
                if tgt[k]["근거"] != old_txt:
                    raise SystemExit(f"ABORT: {k} {name} text differs from the part file")
                tgt[k]["근거"] = new_txt
            if sd["cells"][k].get("page") != old:
                raise SystemExit(f"ABORT: {k} sidecar page differs")
            sd["cells"][k]["page"] = new
            changed.append((k, old, new))
    print("cells to fix:", len(changed), "| sample:", changed[:4])
    if not a.apply:
        print("dry-run -- nothing written")
        return
    rd = L.BACKUP / "round_pagefix"
    rd.mkdir(parents=True, exist_ok=True)
    for p in (L.OVERRIDES, L.SIDECAR):
        shutil.copy2(p, rd / p.name)
    for p in raw_parts:
        shutil.copy2(p, rd / p.name)
    for p, raw in ((L.OVERRIDES, raw_ov), (L.SIDECAR, raw_sd)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read")
    for p, raw in raw_parts.items():
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read")
    for code, (p, obj) in parts.items():
        L.safe_write(p, json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8"))
    L.safe_write(L.SIDECAR, L.dumps(sd, 2, "\r\n"))
    L.safe_write(L.OVERRIDES, L.dumps(ov, 2, "\n"))
    print("APPLIED: page + 근거 p-token corrected for", len(changed), "cells (values untouched)")


if __name__ == "__main__":
    main()
