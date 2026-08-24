# -*- coding: utf-8 -*-
"""Read-only: corroborate KR0094's disclosed item36 on the OTHER axis that consumes it —
19_market (item19 == sqrt(item36..40 . MARKET_M . item36..40)), both 값 and 값_적용후.

The correlation matrix is IMPORTED from the rule engine (never retyped).
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import MARKET_M  # noqa: E402

OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_market_axis.txt"
K_CODE, K_NO, K_Q, K_V, K_VA = "원보험사코드", "항목번호", "공시분기", "값", "값_적용후"

recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
b = {}
for r in recs:
    b.setdefault((r[K_CODE], r[K_Q]), {})[r[K_NO]] = (r.get(K_V), r.get(K_VA))


def num(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


buf = ["MARKET_M shape %s (imported from src/solvency/validation/kics_json_rules.py)"
       % (np.asarray(MARKET_M).shape,)]
buf.append("")
buf.append("%-8s %-9s %-8s %12s %12s %12s %10s" %
           ("code", "quarter", "column", "item19 공시", "sqrt(36-40)", "diff", "rel%"))
for code in ("KR0094", "KR0032"):
    for (c, q), d in sorted(b.items()):
        if c != code:
            continue
        for idx, col in ((0, "값"), (1, "값_적용후")):
            v19 = num(d.get(19, (None, None))[idx])
            subs = [num(d.get(n, (None, None))[idx]) for n in (36, 37, 38, 39, 40)]
            if v19 is None or any(s is None for s in subs):
                continue
            x = np.array(subs, dtype=float)
            calc = float(np.sqrt(x @ np.asarray(MARKET_M, dtype=float) @ x))
            diff = v19 - calc
            rel = diff / v19 * 100 if v19 else float("nan")
            buf.append("%-8s %-9s %-8s %12.2f %12.2f %12.4f %10.4f"
                       % (c, q, col, v19, calc, diff, rel))
    buf.append("")

OUT.write_text("\n".join(buf), encoding="utf-8")
print("wrote", OUT)
