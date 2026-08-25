# -*- coding: utf-8 -*-
"""FY-boundary residual census (post-fix) sorted by ratio-to-tol, plus a tol-tightening
simulation. Companion to inbox/parser/20260825T1340Z (csm_fy_opening_disagrees_across_filings).

read-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
import validate_data_contract as gate  # noqa: E402

recs = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
recs = recs["records"] if isinstance(recs, dict) else recs
wf: dict = {}
for r in recs:
    co, q = r.get("원수사명"), r.get("공시분기")
    if co is None or q is None:
        continue
    wf.setdefault((co, q), {})[str(r.get("항목명") or "").replace(" ", "")] = r.get("값")
by_co: dict = {}
for (co, q), m in wf.items():
    by_co.setdefault(co, {})[q] = m

rows = []
for co, qmap in by_co.items():
    for q in qmap:
        try:
            fy = int(str(q)[:4])
        except ValueError:
            continue
        prev = qmap.get(f"{fy - 1}.4Q")
        if prev is None:
            continue
        pc, op = prev.get("기말CSM"), (qmap.get(q) or {}).get("기초CSM")
        if pc is None or op is None:
            continue
        gap = op - pc
        tol = max(gate.CSM_CONT_TOL_REL * abs(pc), gate.CSM_CONT_TOL_ABS)
        ratio = (abs(gap) / tol) if tol else 0.0
        rows.append((ratio, abs(gap), co, q, pc, op, gap, tol))
rows.sort(reverse=True)

print("=" * 100)
print(f"평가된 경계: {len(rows)}   (tol = max(0.5% * |직전기말|, 2.0억))")
print("=" * 100)
exact0 = sum(1 for r in rows if r[1] == 0.0)
sub_nonzero = [r for r in rows if 0.0 < r[1] and r[0] <= 1.0]
over = [r for r in rows if r[0] > 1.0]
print(f"  잔차 정확히 0        : {exact0}")
print(f"  0 < 잔차 <= tol      : {len(sub_nonzero)}")
print(f"  잔차 > tol           : {len(over)}  (등재된 예외 제외하면 RED)")
print()
print("[tol 대비 비율 상위 20 -- ratio=1.0 이 게이트 문턱]")
for ratio, absgap, co, q, pc, op, gap, tol in rows[:20]:
    reg = "  [등재 예외]" if (co, q) in gate._CSM_CONTINUITY_EXCEPTIONS else ""
    print(f"  ratio={ratio:5.1%}  {co:<16} {q}  직전기말{pc:>10,.1f} -> 기초{op:>10,.1f}  "
          f"Δ{gap:>+9,.2f}  tol={tol:>7,.2f}{reg}")

print()
print("=" * 100)
print("tol 조이기 시뮬레이션 (수치만 -- 실제로 조이지 않음)")
print("=" * 100)
base_rel, base_abs = gate.CSM_CONT_TOL_REL, gate.CSM_CONT_TOL_ABS
scenarios = [
    ("현재       ", base_rel, base_abs),
    ("rel 0.5->0.4%", 0.004, base_abs),
    ("rel 0.5->0.3%", 0.003, base_abs),
    ("rel 0.5->0.2%", 0.002, base_abs),
    ("rel 0.5->0.1%", 0.001, base_abs),
    ("abs 2.0->1.0억", base_rel, 1.0),
    ("abs 2.0->0.5억", base_rel, 0.5),
    ("rel0.2%+abs1.0억", 0.002, 1.0),
]
for label, rel, absf in scenarios:
    breaks = []
    for _ratio, absgap, co, q, pc, op, gap, _tol in rows:
        t = max(rel * abs(pc), absf)
        if absgap > t:
            breaks.append((co, q, gap, t))
    new_only = [b for b in breaks if (b[0], b[1]) not in gate._CSM_CONTINUITY_EXCEPTIONS]
    print(f"  {label}: 총 break={len(breaks):3d}  (신규 미등재={len(new_only)})")
    if rel != base_rel or absf != base_abs:
        for co, q, gap, t in new_only:
            print(f"      NEW  {co:<16} {q}  Δ{gap:+,.2f}  tol={t:,.2f}")
