#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provenance wording fix for the 27 equity-table gap-fill cells (2026-10-11, parser/ifrs17).

These BS cells were read from the PRIOR-QUARTER column of the next filing's "B/S상 자기자본" table (the table prints three
quarter columns).  The part files carried the right `pdf`/`page`, but the `근거` text said "정기경영공시 <cell quarter>", i.e. it
named the wrong filing.  This script rewrites ONLY that prefix of the 근거 string for the cells this ticket added
(load_manifest_bs.json), in the three places the loader wrote them:
  data/_derived/bs_from_disclosure_parts/<KR>_agent_gran.json   (cells[k].근거)
  data/_derived/bs_from_disclosure.json                          (cells[k].근거)
  data/dart/viz/bs_manual_overrides.json                         (cells[k].근거)
Values, keys, row order and every other byte are untouched (byte-exact round trip is verified before writing, the files are
re-read right before the write, backups go to data/_derived/bspl_granularity_backup_20261011/round_basisfix/).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_fix_basis.py [--apply]
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

PREFIX = re.compile(r"^정기경영공시 (\d{4}\.\dQ) B/S상 자기자본 p(\d+) ")


def new_text(old: str, cell_q: str, pdf: str) -> str | None:
    m = PREFIX.match(old)
    fy = re.search(r"FY(\d{4})_(Q\d)", pdf or "")
    if not m or not fy or m.group(1) != cell_q:
        return None
    filing_q = f"{fy.group(1)}.{fy.group(2)[1]}Q"
    if filing_q == cell_q:
        return None
    return (f"정기경영공시 {filing_q} 공시본 B/S상 자기자본 표 p{m.group(2)} 의 전분기 열({cell_q} 값; 그 열의 자본총계 = 구성 "
            f"항목 합이 닫히는 것을 확인) " + old[m.end():])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    man = json.loads(L.MANIFEST.read_text(encoding="utf-8"))
    mine = set()
    for r in man["rounds"]:
        mine |= set(r["added"])

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
            if k not in mine:
                continue
            q = k.split("|")[2]
            nt = new_text(cell["근거"], q, cell.get("pdf"))
            if nt is None:
                continue
            changed.append((k, cell["근거"][:70], nt[:130]))
            old = cell["근거"]
            cell["근거"] = nt
            for tgt, name in ((ov["cells"], "overlay"), (sd["cells"], "sidecar")):
                if k not in tgt:
                    raise SystemExit(f"ABORT: {k} missing in {name}")
                if tgt[k]["근거"] != old:
                    raise SystemExit(f"ABORT: {k} {name} text differs from the part file; refusing")
                tgt[k]["근거"] = nt
    print("cells to rewrite:", len(changed))
    for k, o, n in changed[:6]:
        print("  ", k, "|", o, "->", n)
    if not a.apply:
        print("dry-run -- nothing written")
        return

    rd = L.BACKUP / "round_basisfix"
    rd.mkdir(parents=True, exist_ok=True)
    for p in (L.OVERRIDES, L.SIDECAR):
        shutil.copy2(p, rd / p.name)
    for p in raw_parts:
        shutil.copy2(p, rd / p.name)
    # re-read guard
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
    print("APPLIED: rewrote the 근거 prefix of", len(changed), "cells in part files, sidecar and overlay (values untouched)")


if __name__ == "__main__":
    main()
