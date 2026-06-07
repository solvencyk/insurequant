# -*- coding: utf-8 -*-
"""Probe: dump caption strings containing a keyword across a company's yearly filings,
to find quarter-agnostic anchors for generalizing the per-company Tier-2 handlers."""
import sys
import glob
import os
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

CODE = sys.argv[1] if len(sys.argv) > 1 else "KR0003"
KW = sys.argv[2:] if len(sys.argv) > 2 else ["보험손익", "재보험손익"]


def xmls_in(d):
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


for fy in ("FY2023_Q4", "FY2024_Q4", "FY2025_Q4"):
    dirs = glob.glob(f"data/dart/{fy}/raw/{CODE}_*")
    print(f"\n===== {fy} ({CODE}) =====")
    for d in dirs:
        for x in xmls_in(d):
            try:
                tabs = _iter_tables_with_context(Path(x))
            except Exception as e:
                print("  parse-err", e)
                continue
            for t in tabs:
                cap = t.caption or ""
                if any(k in cap for k in KW):
                    hb = " ".join(" ".join(h) for h in t.header)[:80]
                    print(f"  CAP: {cap[:110]}")
