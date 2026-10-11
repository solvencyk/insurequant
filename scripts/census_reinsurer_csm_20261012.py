# -*- coding: utf-8 -*-
"""Read-only census of what the four CSM-family masters hold for the 8 reinsurers (KR1101..KR1108) x 14 quarters.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/census_reinsurer_csm_20261012.py [--root DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODES = [f"KR11{n:02d}" for n in range(1, 9)]
QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + ["2026.1Q", "2026.2Q"]
NAMES = {"KR1101": "뮌헨", "KR1102": "스위스리", "KR1103": "제네럴", "KR1104": "하노버", "KR1105": "RGA", "KR1106": "스코리", "KR1107": "퍼시픽", "KR1108": "마이브라운"}


def load(root: Path, name: str):
    return json.loads((root / name).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = Path(a.root)
    sys.stdout.reconfigure(encoding="utf-8")
    wf, am, se, il = (load(root, n) for n in ("CSM_waterfall.json", "CSM_amortization.json", "CSM_sensitivity.json", "insurance_liability_portfolio.json"))
    out = {}
    lines = []

    def emit(s=""):
        lines.append(s)

    # waterfall: items present per (code, q)
    w = defaultdict(set)
    for r in wf:
        if r["원보험사코드"] in CODES and r.get("값") is not None:
            w[(r["원보험사코드"], r["공시분기"])].add(r["항목번호"])
    emit("== CSM_waterfall: items with value (1..6) per company x quarter  ('.' none, '6' all six, else item list)")
    emit("code  name        " + " ".join(q[2:] for q in QUARTERS))
    for c in CODES:
        cells = []
        for q in QUARTERS:
            s = w.get((c, q), set())
            cells.append("." if not s else ("6" if s == {1, 2, 3, 4, 5, 6} else "".join(map(str, sorted(s)))))
        emit(f"{c} {NAMES[c]:<8} " + " ".join(f"{x:>6}" for x in cells))
    out["waterfall"] = {f"{c}|{q}": sorted(w.get((c, q), [])) for c in CODES for q in QUARTERS}
    # amortization
    m = defaultdict(set)
    for r in am:
        if r["원보험사코드"] in CODES and r.get("상각액") is not None:
            m[(r["원보험사코드"], r["공시분기"])].add(r["경과차년"])
    emit("\n== CSM_amortization: number of years with value (of 1..10)")
    emit("code  name        " + " ".join(q[2:] for q in QUARTERS))
    for c in CODES:
        emit(f"{c} {NAMES[c]:<8} " + " ".join(f"{(str(len(m[(c,q)])) if (c,q) in m else '.'):>6}" for q in QUARTERS))
    out["amortization"] = {f"{c}|{q}": sorted(m.get((c, q), [])) for c in CODES for q in QUARTERS}
    # sensitivity
    s = defaultdict(list)
    for r in se:
        if r["원보험사코드"] in CODES:
            s[(r["원보험사코드"], r["공시분기"])].append(r)
    emit("\n== CSM_sensitivity: rows (nonnull CSM변동 / total)")
    emit("code  name        " + " ".join(q[2:] for q in QUARTERS))
    for c in CODES:
        cells = []
        for q in QUARTERS:
            rs = s.get((c, q), [])
            cells.append("." if not rs else f"{sum(1 for r in rs if r.get('CSM변동') is not None)}/{len(rs)}")
        emit(f"{c} {NAMES[c]:<8} " + " ".join(f"{x:>6}" for x in cells))
    out["sensitivity"] = {f"{c}|{q}": [(r["순번"], r["위험구분"], r["충격수준"], r.get("CSM변동"), r.get("당기손익영향"), r.get("자본영향")) for r in s.get((c, q), [])] for c in CODES for q in QUARTERS}
    # ILP items
    il_items = defaultdict(set)
    names = {}
    for r in il:
        if r["원보험사코드"] in CODES and r.get("값") is not None:
            il_items[(r["원보험사코드"], r["공시분기"])].add(r["항목번호"])
        names[r["항목번호"]] = r["항목명"]
    emit("\n== ILP: count of items with value (of 1..17 incl. 16/17)  ; item names: " + str({k: names[k] for k in sorted(names)}))
    emit("code  name        " + " ".join(q[2:] for q in QUARTERS))
    for c in CODES:
        emit(f"{c} {NAMES[c]:<8} " + " ".join(f"{(str(len(il_items[(c,q)])) if (c,q) in il_items else '.'):>6}" for q in QUARTERS))
    out["ilp"] = {f"{c}|{q}": sorted(il_items.get((c, q), [])) for c in CODES for q in QUARTERS}
    txt = "\n".join(lines)
    print(txt)
    if a.out:
        Path(a.out).write_text(txt + "\n", encoding="utf-8", newline="\n")
        Path(a.out).with_suffix(".json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
