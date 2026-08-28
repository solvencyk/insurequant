#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect KB손해보험(00120216) OFS vs CFS cache content for FY2024/2025 annual filings --
does OFS have items 1/2/3 (would block CFS fallback) and does either basis carry
dart_GuranteeReserve (item8, 보증준비금)? Read-only probe for inbox/parser/20260828T2350Z."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "dart" / "_fs_api_cache"

ACCOUNT_IDS_CORE = {
    1: "ifrs-full_Assets", 2: "ifrs-full_Liabilities", 3: "ifrs-full_Equity",
}
GUARANTEE = ("dart_GuranteeReserve", "dart_GuranteeReserveToBeAdded")


def load(fn):
    p = CACHE / fn
    if not p.exists():
        print(f"  {fn}: MISSING")
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("status") != "000":
        print(f"  {fn}: status={d.get('status')} msg={d.get('message')}")
        return []
    return d.get("list") or []


def summarize(fn):
    lst = load(fn)
    if not lst:
        return
    print(f"  {fn}: {len(lst)} rows")
    core = {}
    for a in lst:
        if a.get("sj_div") != "BS" or a.get("account_detail") != "-":
            continue
        aid = a.get("account_id")
        for item, want in ACCOUNT_IDS_CORE.items():
            if aid == want:
                core[item] = a.get("thstrm_amount")
        if aid in GUARANTEE or (a.get("account_nm") or "").replace(" ", "").find("보증준비금") >= 0:
            print(f"    GUARANTEE-hit: account_id={aid!r} account_nm={a.get('account_nm')!r}"
                  f" thstrm_amount={a.get('thstrm_amount')!r}")
    print(f"    core items 1/2/3 present: {sorted(core.keys())} -> {core}")


for fn in (
    "00120216_2024_11011_OFS.json", "00120216_2024_11011_CFS.json",
    "00120216_2025_11011_OFS.json", "00120216_2025_11011_CFS.json",
    "00120216_2026_11011_OFS.json", "00120216_2026_11011_CFS.json",
    "00120216_2026_11012_OFS.json", "00120216_2026_11013_OFS.json",
):
    print(f"=== {fn} ===")
    summarize(fn)
