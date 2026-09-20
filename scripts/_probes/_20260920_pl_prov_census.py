#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Census for the PL_breakdown provenance sidecar re-issue (inbox 20260918T0700Z E).

Measures, offline:
  1. master PL_breakdown.json cell grid (company, quarter, item_block) + which items carry
     a non-null 값 in each block
  2. raw DART filing dirs available per (code, quarter)
  3. FS-API cache files available per (corp_code, year, reprt, fs_div)
  4. gold overlay cells (data/_gold/user_pl_cells.json) and _GOLD_CELL_OVERRIDE keys

Writes data/_derived/_probe_20260920_pl_prov_census.json.  Read-only on everything else.
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

PL_CONTRACT_NOTES = {4, 5, 6, 9, 10, 11, 13, 14}


def _block(it):
    return "contract_notes" if it in PL_CONTRACT_NOTES else "income_statement"


def main():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    print(f"master rows = {len(rows)}")

    codes = {}
    blocks = defaultdict(lambda: {"items": set(), "nonnull": set(), "null": set()})
    quarters = set()
    bad_item = 0
    for r in rows:
        code, q, name = r.get("원보험사코드"), r.get("공시분기"), r.get("원수사명")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            bad_item += 1
            continue
        if not (code and q):
            bad_item += 1
            continue
        codes[code] = name
        quarters.add(q)
        b = blocks[(code, q, _block(it))]
        b["items"].add(it)
        if r.get("값") is None:
            b["null"].add(it)
        else:
            b["nonnull"].add(it)

    print(f"bad/skipped rows = {bad_item}")
    print(f"companies = {len(codes)}  quarters = {len(quarters)}  cells = {len(blocks)}")
    print(f"quarters sorted = {sorted(quarters)}")
    bc = Counter(k[2] for k in blocks)
    print(f"cells by block = {dict(bc)}")
    empty = [k for k, v in blocks.items() if not v["nonnull"]]
    print(f"cells with ZERO non-null 값 = {len(empty)}")
    print(f"  by block = {dict(Counter(k[2] for k in empty))}")

    # ---- raw filing dirs ----
    raw = defaultdict(list)
    for base in sorted(glob.glob(str(ROOT / "data/dart/FY*/raw"))):
        m = re.search(r"FY(\d{4})_Q(\d)", base.replace("\\", "/"))
        if not m:
            continue
        q = f"{m.group(1)}.{m.group(2)}Q"
        for d in sorted(glob.glob(base + "/KR*")):
            b = os.path.basename(d)
            mm = re.match(r"(KR\d+)_", b)
            if not mm:
                continue
            xmls = sorted(set(glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml")
                              + glob.glob(d + "/extracted*/*.xml")))
            raw[(mm.group(1), q)].append({
                "dir": os.path.relpath(d, ROOT).replace("\\", "/"),
                "xmls": [os.path.relpath(x, ROOT).replace("\\", "/") for x in xmls],
            })
    print(f"\nraw (code,quarter) groups = {len(raw)}")
    multi = {k: len(v) for k, v in raw.items() if len(v) > 1}
    print(f"  groups with >1 rcept dir = {len(multi)}")
    noxml = [k for k, v in raw.items() if not any(e["xmls"] for e in v)]
    print(f"  groups with NO xml at all = {len(noxml)} -> {sorted(noxml)[:12]}")
    nx = Counter(len(e["xmls"]) for v in raw.values() for e in v)
    print(f"  xml-count histogram per dir = {dict(sorted(nx.items()))}")

    # ---- FS-API cache ----
    cache = sorted(os.path.basename(p) for p in
                   glob.glob(str(ROOT / "data/dart/_fs_api_cache/*.json")))
    print(f"\nfs_api_cache files = {len(cache)}")
    cc_set = sorted({c.split("_")[0] for c in cache})
    print(f"  distinct corp_code = {len(cc_set)}")

    # ---- gold overlay ----
    gp = ROOT / "data/_gold/user_pl_cells.json"
    gold = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else {}
    gs = gold.get("set", [])
    print(f"\nuser_pl_cells.json set entries = {len(gs)}")
    gkeys = {(s.get("원보험사코드"), s.get("공시분기"), _block(int(s["항목번호"])))
             for s in gs if str(s.get("항목번호", "")).strip().isdigit()}
    print(f"  distinct (code,quarter,block) = {len(gkeys)}")

    # ---- coverage: which master cells have raw / which don't ----
    have_raw = sum(1 for (c, q, b) in blocks if (c, q) in raw)
    print(f"\nmaster cells whose (code,quarter) has a raw filing dir = {have_raw}/{len(blocks)}")
    no_raw_codes = Counter(c for (c, q, b) in blocks if (c, q) not in raw)
    print(f"  cells with NO raw dir, by company = {dict(no_raw_codes)}")

    out = {
        "master_rows": len(rows),
        "companies": codes,
        "quarters": sorted(quarters),
        "cells": [{"company_code": c, "quarter": q, "item_block": b,
                   "items": sorted(v["items"]),
                   "nonnull_items": sorted(v["nonnull"]),
                   "null_items": sorted(v["null"])}
                  for (c, q, b), v in blocks.items()],
        "raw_index": {f"{c}|{q}": v for (c, q), v in raw.items()},
        "fs_api_cache_files": cache,
        "gold_block_keys": sorted(f"{a}|{b}|{c}" for (a, b, c) in gkeys),
    }
    dst = ROOT / "data/_derived/_probe_20260920_pl_prov_census.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {dst.relative_to(ROOT)}")


main()
