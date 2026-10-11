# -*- coding: utf-8 -*-
"""Step 99 (read-only): which 값_당분기 convention does CSM_waterfall.json actually use?  Measured on every company, three named ones shown first.

Convention under test (build_root_masters.build_csm):
  item 6 (closing, stock)  : 값_당분기 == 값
  item 1 (opening, stock)  : Q1 -> 값 ; otherwise the previous quarter's item-6 값 (None if that quarter is not in the master)
  items 2..5 (flows)      : Q1 -> 값 ; otherwise 값(q) - 값(previous quarter), rounded to 6 decimals (None if the previous quarter is missing)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.stdout.reconfigure(encoding="utf-8")

rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
ytd = defaultdict(dict)       # (code, item) -> {q: 값}
stored = defaultdict(dict)    # (code, item) -> {q: 값_당분기}
names = {}
for r in rows:
    ytd[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
    stored[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r.get("값_당분기")
    names[r["원보험사코드"]] = r["원수사명"]


def prev_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


def expected(code, item, q):
    v = ytd[(code, item)].get(q)
    if v is None:
        return "skip"
    p = prev_q(q)
    if item == 6:
        return v
    if item == 1:
        if p is None:
            return v
        return ytd[(code, 6)].get(p)
    if p is None:
        return v
    pv = ytd[(code, item)].get(p)
    return None if pv is None else round(v - pv, 6)


def check(code):
    stats = {"match": 0, "mismatch": 0, "skip": 0, "none_both": 0}
    bad = []
    for item in range(1, 7):
        for q, v in ytd[(code, item)].items():
            e = expected(code, item, q)
            if e == "skip":
                stats["skip"] += 1
                continue
            s = stored[(code, item)].get(q)
            ok = (s is None and e is None) or (s is not None and e is not None and abs(s - e) < 1.5e-6)
            if ok:
                stats["match"] += 1
                if e is None:
                    stats["none_both"] += 1
            else:
                stats["mismatch"] += 1
                bad.append((q, item, s, e))
    return stats, bad


for code in ["KR0001", "KR0003", "KR0005"]:
    st, bad = check(code)
    print(f"{code} {names[code]}: {st}  mismatches: {bad[:6]}")
print("\nall companies:")
tot = defaultdict(int)
worst = []
for code in sorted({c for c, _ in ytd}):
    st, bad = check(code)
    for k, v in st.items():
        tot[k] += v
    if bad:
        worst.append((code, names[code], len(bad), bad[:3]))
print(dict(tot))
print("companies with at least one mismatch:", len(worst))
for w in worst[:14]:
    print("  ", w)
# the cells of Lina this is about
print("\nKR0074 rows with stored None where the convention gives a value:")
for item in range(1, 6):
    for q, v in sorted(ytd[("KR0074", item)].items()):
        e = expected("KR0074", item, q)
        s = stored[("KR0074", item)].get(q)
        if s is None and e is not None and e != "skip":
            print(f"  {q} item {item}: stored None -> convention {e}")
