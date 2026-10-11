#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 2 side finding: which 8-1 line is KR1000's master item 10 (현금및현금성자산)?

Compares, for every quarter, the master item 10 / 24 with the K-statement lines of the same filing's 별도 8-1 table
(현금및현금성자산, 예치금, 기타부채) -- read-only.  Output -> data/_derived/bspl_followup_20261011/kr1000_item10_24_definition.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402

OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "kr1000_item10_24_definition.json"
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
LAB = {"cash": ("현금및현금성자산",), "dep": ("예치금",), "other_liab": ("기타부채",)}


def norm(s):
    return "".join(ch for ch in s if not ch.isspace()).lstrip("ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ.0123456789")


def main():
    all_v, anchor, disc, meta = B.load_master()
    mv = all_v["KR1000"]
    out = []
    for q in QS:
        doc = B.load_tables("KR1000", q)
        rec = {"quarter": q, "master10": mv.get((10, q)), "master24": mv.get((24, q))}
        if doc:
            for t in B.pick_tables(doc, "bs_full"):
                lines = {}
                for r in t["rows"]:
                    n = norm(r["label"])
                    for k, labs in LAB.items():
                        if n in labs and k not in lines and r["vals"]:
                            lines[k] = r["vals"][0]
                if lines:
                    unit = t.get("unit")
                    f = B.UNIT_FACTOR.get(unit, 1e-6)
                    rec["table"] = {"page": t["page"], "unit": unit, "basis": t.get("basis")}
                    rec.update({f"K_{k}": round(v * f, 6) for k, v in lines.items()})
                    break
        out.append(rec)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{'q':8} {'master10':>14} {'K cash':>14} {'K 예치금':>14} | {'master24':>12} {'K 기타부채(first)':>18}")
    for r in out:
        def f(x):
            return f"{x:14,.2f}" if isinstance(x, (int, float)) else f"{'-':>14}"
        print(f"{r['quarter']:8} {f(r['master10'])} {f(r.get('K_cash'))} {f(r.get('K_dep'))} | {f(r['master24'])[2:]:>12} {f(r.get('K_other_liab'))}")


if __name__ == "__main__":
    main()
