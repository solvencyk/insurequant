# -*- coding: utf-8 -*-
"""Dump full rows of tables whose caption contains a keyword, for one (code, FYdir)."""
import sys
import glob
import os
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

CODE, FYDIR, KW = sys.argv[1], sys.argv[2], sys.argv[3]


def xmls_in(d):
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


tables = []
for d in glob.glob(f"data/dart/{FYDIR}/raw/{CODE}_*"):
    for x in xmls_in(d):
        try:
            tables.extend(_iter_tables_with_context(Path(x)))
        except Exception:
            pass

seen = set()
for t in tables:
    cap = t.caption or ""
    if KW not in cap or cap in seen:
        continue
    seen.add(cap)
    hb = " | ".join(" ".join(h) for h in t.header)
    print(f"\n### CAP: {cap[:120]}")
    print(f"    HDR: {hb[:160]}")
    for r in t.rows[:40]:
        cells = [str(c)[:22] for c in r]
        print("    ROW:", cells)
