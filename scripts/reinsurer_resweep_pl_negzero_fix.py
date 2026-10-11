#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cosmetic fix of the rows added by scripts/reinsurer_resweep_pl_apply.py: a printed '(0)' / rounded negative zero was stored as -0.0 (JSON `-0.0`); store 0.0.
Touches ONLY rows whose key is in the re-sweep fill plan and whose 값 / 값_당분기 is -0.0.  Equality is unchanged (-0.0 == 0.0); this only removes the minus sign.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_pl_negzero_fix.py [--apply]
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_granularity_load_bs as L  # noqa: E402

MASTER = ROOT / "PL_breakdown.json"
PLAN = ROOT / "data/_derived/reinsurer_resweep_20261012/fill_plan.json"


def negzero(v):
    return isinstance(v, float) and v == 0.0 and math.copysign(1.0, v) < 0


def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))["plan"]
    keys = {(p["co"], str(p["item"]), p["q"]) for p in plan}
    rows, raw = L.load_json_exact(MASTER, 1, "\r\n")
    n = 0
    for r in rows:
        k = (r["원보험사코드"], str(r["항목번호"]), r["공시분기"])
        for f in ("값", "값_당분기"):
            if negzero(r.get(f)):
                if k not in keys:
                    continue           # pre-existing -0.0 of other rows: not ours, left untouched
                r[f] = 0.0
                n += 1
                print("  fix", k, f)
    print(f"{n} fields")
    if "--apply" in sys.argv and n:
        if MASTER.read_bytes() != raw:
            raise SystemExit("ABORT: changed since read")
        L.safe_write(MASTER, L.dumps(rows, 1, "\r\n"))
        print("APPLIED")


if __name__ == "__main__":
    main()
