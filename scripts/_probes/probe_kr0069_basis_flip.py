#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Identify KR0069 and inspect why its 2024 quarters' BS values changed on rebuild --
is this an OFS<->CFS basis flip? Read-only probe for inbox/parser/20260828T2350Z."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

d = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
seen = {}
for r in d:
    c = r.get("원보험사코드")
    if c and c not in seen:
        seen[c] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))
print("KR0069:", seen.get("KR0069"))

sys.path.insert(0, str(ROOT))
from scripts.fetch_dart_fs import resolve_corp, REPRT

NAME_OVERRIDE = {"KR0029": "AIG"}
name = seen["KR0069"][0]
cc = resolve_corp(NAME_OVERRIDE.get("KR0069", name))
print("corp_code:", cc)

CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
files = sorted(CACHE.glob(f"{cc}_2024_*_*.json"))
print(f"{len(files)} 2024 cache files for {cc}:")
for f in files:
    print(" ", f.name)

ACCOUNT_IDS_CORE = {1: "ifrs-full_Assets", 2: "ifrs-full_Liabilities", 3: "ifrs-full_Equity"}


def summarize(fn):
    p = CACHE / fn
    if not p.exists():
        print(f"    {fn}: MISSING")
        return
    dd = json.loads(p.read_text(encoding="utf-8"))
    if dd.get("status") != "000":
        print(f"    {fn}: status={dd.get('status')}")
        return
    lst = dd.get("list") or []
    core = {}
    for a in lst:
        if a.get("sj_div") != "BS" or a.get("account_detail") != "-":
            continue
        aid = a.get("account_id")
        for item, want in ACCOUNT_IDS_CORE.items():
            if aid == want:
                core[item] = a.get("thstrm_amount")
    print(f"    {fn}: {len(lst)} rows, core 1/2/3={core}")


for reprt in ("11011", "11012", "11013", "11014"):
    for basis in ("OFS", "CFS"):
        summarize(f"{cc}_2024_{reprt}_{basis}.json")

print()
print("git history of OFS files:")
import subprocess
for reprt in ("11011", "11012", "11013", "11014"):
    for basis in ("OFS", "CFS"):
        fn = f"data/dart/_fs_api_cache/{cc}_2024_{reprt}_{basis}.json"
        out = subprocess.run(["git", "log", "--oneline", "--follow", "--", fn],
                              cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8")
        lines = out.stdout.strip().splitlines()
        print(f"  {fn}: {len(lines)} commits -- {lines[:3]}{'...' if len(lines) > 3 else ''}")
