#!/usr/bin/env python3
"""Measure how many mmult cells pass ONLY because of the 5% dynamic tolerance band.

Owner decision input (2026-08-21). `validate_kics_disclosure.py` uses
`max(_eff_tol(c), 0.05*abs(exp))` for the 8_life(item17) / 19_market(item19) axes —
this is **parity with the rule engine's 적용전 tolerance**, not a post-column regression:
`kics_json_rules` rules 8_life and 19_market use the same `max(2.0, 0.05*|expected|)`.
Both columns are equally loose. On 삼성화재's scale 5% is ~3,590억.

This script does NOT change anything. It reports, per company × axis × column, the cells
that are inside the 5% band but outside the flat band, so the owner can decide with numbers
whether to tighten. Tightening moves `tests/test_kics_rules_golden.py`.

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/tolerance_band_5pct_audit.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE, KEY_ITEM, KEY_NAME, KEY_QUARTER, KEY_VALUE, KEY_VALUE_POST,
    MARKET_M, R7, _diversified_sqrt,
)
from validate_kics_disclosure import _eff_tol  # noqa: E402

# 행렬은 룰엔진에서 import(재타이핑 금지). 축 15(R4)는 flat tol 이라 이 감사 대상이 아니다.
AXES = {17: (list(range(29, 36)), R7, "8_life"),
        19: (list(range(36, 41)), MARKET_M, "19_market")}


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main() -> int:
    records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    byq, name = {}, {}
    for r in records:
        c, q, it = r.get(KEY_CODE), r.get(KEY_QUARTER), r.get(KEY_ITEM)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    rows = []          # (company, axis, column, quarter, disclosed, expected, diff, flat_tol, dyn_tol)
    evaluated = defaultdict(int)
    for (c, q), m in sorted(byq.items()):
        for parent, (subs, mat, label) in AXES.items():
            for col, i in (("적용전", 0), ("적용후", 1)):
                pv = m.get(parent, (None, None))[i]
                sv = [m.get(x, (None, None))[i] for x in subs]
                if pv is None or any(v is None for v in sv):
                    continue
                evaluated[(label, col)] += 1
                exp = _diversified_sqrt(np.array(sv, dtype=float), mat)
                diff = abs(pv - exp)
                flat = _eff_tol(c)
                dyn = max(flat, 0.05 * abs(exp))
                if flat < diff <= dyn:
                    rows.append((c, name.get(c, c), label, col, q, pv, exp, diff, flat, dyn))

    print("=" * 96)
    print("5%-BAND AUDIT — cells that pass ONLY because tol = max(eff_tol, 5%·|expected|)")
    print("  (measurement only; tolerance NOT changed — owner decision, moves the golden matrix)")
    print("=" * 96)
    print(f"evaluated cells per axis×column: "
          f"{ {f'{k[0]}/{k[1]}': v for k, v in sorted(evaluated.items())} }")
    print(f"cells inside the 5% band but outside flat tol: {len(rows)}")
    print()
    by_axis = defaultdict(list)
    for row in rows:
        by_axis[(row[2], row[3])].append(row)
    for key in sorted(by_axis):
        rs = by_axis[key]
        tot = evaluated[key]
        print(f"--- {key[0]} / {key[1]} : {len(rs)} cells "
              f"({100.0*len(rs)/tot if tot else 0:.1f}% of {tot} evaluated) ---")
        by_co = defaultdict(list)
        for r in rs:
            by_co[(r[0], r[1])].append(r)
        for (code, nm), crs in sorted(by_co.items(), key=lambda kv: -max(r[7] for r in kv[1])):
            worst = max(crs, key=lambda r: r[7])
            qs = ", ".join(sorted(r[4] for r in crs))
            print(f"   {code} {nm:24s} n={len(crs):>2}  max|diff|={worst[7]:>12,.1f}억  "
                  f"(flat_tol={worst[8]:.1f} · dyn_tol={worst[9]:,.1f} @ {worst[4]})")
            print(f"        quarters: {qs}")
        print()
    if not rows:
        print("  (none — every evaluated cell closes inside the flat tolerance too)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
