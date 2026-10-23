# -*- coding: utf-8 -*-
"""read-only: evidence for the documented live-vs-baseline pairs (LIVE_VS_BASE_OK of e23_apply.py): for KR0072 2023.2Q/3Q items 7 and 12 and 2023.2Q item 16 -- live master value, value of a FRESH build_pl() with the live gold,
the formula value from the LIVE legs (7 = 3-(4+5+6), 12 = 8-(9+10+11)), and the gold entry value.  Plus the KR0072 drift cells of drift_before.json."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8")
import e23_apply as A  # noqa: E402

ROOT = A.ROOT
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
base = A.simulate_rows(gold, "c05")
L = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in live}
B = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in base}
G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
print("KR0072: live master value | value of a fresh build_pl() with the live gold | formula value from the LIVE legs | gold entry")
for k, (lv, bs) in sorted(A.LIVE_VS_BASE_OK.items()):
    c, i, q = k
    g = lambda j: L[(c, j, q)]["값"]  # noqa: E731
    form = None
    if i == 7:
        form = g(3) - (g(4) + g(5) + g(6))
    elif i == 12:
        form = g(8) - (g(9) + g(10) + g(11))
    print(f"  {q} i{i:>2}: live {L[k]['값']!r:>22} | fresh build {B[k]['값']!r:>22} | formula(live legs) {form!r:>22} | gold {G[k]['값'] if k in G else None!r:>22}")
    assert A.same(L[k]["값"], lv) and A.same(B[k]["값"], bs), (k, L[k]["값"], B[k]["값"], lv, bs)
    if form is not None:
        assert abs(form - L[k]["값"]) <= 1e-6, (k, form, L[k]["값"])
print("all documented pairs reproduced; for items 7 / 12 the live cell equals the formula value of the live legs (hand-corrected after the A2 leg fix), the fresh build does not")
sj = json.loads((HERE / "drift_before.json").read_text(encoding="utf-8"))
kd = sorted([x for x in sj["drift_all"] if x[0] == "KR0072"], key=lambda x: (x[2], x[1]))
print(f"drift_before.json: KR0072 drift cells (live != fresh build with the live gold): {len(kd)}")
by = {}
for c, i, q in kd:
    by.setdefault(q, []).append(i)
for q in sorted(by):
    print("   ", q, by[q])
