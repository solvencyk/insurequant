#!/usr/bin/env python3
"""SIMULATION ONLY — what does validate_data_contract report if
_DISPLAY_QUARTERS includes 2026.2Q?  Writes nothing (the gate has no writes).

Runs main() twice in-process and diffs the finding sets.
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as G  # noqa: E402

ORIG = set(G._DISPLAY_QUARTERS)


def snapshot(label):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = G.main([])
    out = buf.getvalue()
    reds = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("RED ")]
    yels = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("YELLOW ")]
    summ = next((ln for ln in out.splitlines() if ln.startswith("SUMMARY")), "")
    print(f"\n### {label}: exit={rc}  {summ.strip()}")
    return rc, set(reds), set(yels), out


rc0, r0, y0, out0 = snapshot("BEFORE (_DISPLAY_QUARTERS 현행, 2026.1Q 까지)")

G._DISPLAY_QUARTERS = ORIG | {"2026.2Q"}
rc1, r1, y1, out1 = snapshot("AFTER  (_DISPLAY_QUARTERS + 2026.2Q)")

print("\n" + "=" * 78)
print(f"DELTA  RED +{len(r1 - r0)} / -{len(r0 - r1)}   YELLOW +{len(y1 - y0)} / -{len(y0 - y1)}")
print("=" * 78)
for r in sorted(r1 - r0):
    print("  NEW RED    ", r[:220])
for r in sorted(r0 - r1):
    print("  GONE RED   ", r[:220])
for r in sorted(y1 - y0):
    print("  NEW YELLOW ", r[:220])
for r in sorted(y0 - y1):
    print("  GONE YELLOW", r[:220])
