#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-off probe for inbox/parser/20260828T2350Z ticket: identify which company/quarter
the 7 new item8 (보증준비금 적립액) cells belong to, before touching IFRS17_BS.json.
Read-only: only reads kics_disclosure.json, data/_fs_api_cache, IFRS17_BS.json (disk copy).
"""
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

for kr in ("KR0010",):
    print(kr, seen.get(kr))

sys.path.insert(0, str(ROOT))
from scripts.fetch_dart_fs import resolve_corp

NAME_OVERRIDE = {"KR0029": "AIG"}
name = seen["KR0010"][0]
cc = resolve_corp(NAME_OVERRIDE.get("KR0010", name))
print("corp_code:", cc)

CACHE = ROOT / "data" / "dart" / "_fs_api_cache"
files = sorted(CACHE.glob(f"{cc}_*_*_*.json"))
print(f"{len(files)} cache files for {cc}:")
for f in files:
    print(" ", f.name)
