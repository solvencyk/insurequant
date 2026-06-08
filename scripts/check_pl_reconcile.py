# -*- coding: utf-8 -*-
"""PL Tier-2 RECONCILIATION census — uses the PROJECT's bridge identities verbatim
(same as validate_master_tables.PL_EQS, incl. dual-form 보험손익 and the 기타원수/기타재보
terms), so it agrees with the gate instead of inventing weaker identities.

For every (company, quarter) and every bridge equation it classifies into:
  WRONG   — LHS present, ALL RHS terms present, but |Σ−LHS| over tolerance  → parser bug
            (this is what the user caught on 농협: a breakdown that does not add up)
  HOLE    — LHS present and SOME RHS terms present, but ≥1 RHS term is None  → the stacked
            bar has a missing slice; if the filing disclosed it, it's a parser gap
  ABSENT  — LHS present but NO RHS term present                            → not decomposed
  (PASS / LHS-absent are silent)

Run:  python scripts/check_pl_reconcile.py            (summary + WRONG + HOLE detail)
      python scripts/check_pl_reconcile.py --wrong    (only WRONG, machine-friendly)
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
PL = ROOT / "PL_breakdown.json"

DEFAULT_FLOOR = 200.0          # 백만원, matches validate_master_tables
EQ_FLOOR = {"영업이익=보험+투자": 600.0}   # match the label used in EQS below

# (short label, LHS item#, [(RHS item#, sign), ...])
EQS = [
    ("원수손익=4+5+6+7", 3, [(4, 1), (5, 1), (6, 1), (7, 1)]),
    ("재보손익=9+10+11+12", 8, [(9, 1), (10, 1), (11, 1), (12, 1)]),
    ("장기손익=원수+재보", 2, [(3, 1), (8, 1)]),
    ("투자손익=18+19", 17, [(18, 1), (19, 1)]),
    ("영업이익=보험+투자", 20, [(1, 1), (17, 1)]),
    ("세전=영업+영업외", 22, [(20, 1), (21, 1)]),
    ("당기순=세전-법인세", 24, [(22, 1), (23, -1)]),
]


def asnum(x):
    try:
        return int(x)
    except Exception:
        return None


def main(argv) -> int:
    only_wrong = "--wrong" in argv
    rows = json.loads(PL.read_text(encoding="utf-8"))
    cell: dict[tuple, dict] = defaultdict(dict)
    name_of: dict[str, str] = {}
    for r in rows:
        it = asnum(r["항목번호"])
        if it is None:
            continue
        name_of[r["원보험사코드"]] = r["원수사명"]
        cell[(r["원보험사코드"], r["공시분기"])][it] = r.get("값")

    wrong = []   # (co, q, label, lhs, rhs, gap)
    hole = []    # (co, q, label, lhs, present_terms, missing_terms)
    for (code, q), d in cell.items():
        for label, lk, terms in EQS:
            lhs = d.get(lk)
            if lhs is None:
                continue
            present = [(i, s) for i, s in terms if d.get(i) is not None]
            missing = [i for i, _ in terms if d.get(i) is None]
            if not present:
                continue  # ABSENT — not decomposed at all
            if missing:
                # HOLE only matters if the disclosed slices are non-trivial
                hole.append((code, q, label, lhs, [i for i, _ in present], missing))
                continue
            rhs = sum(s * d[i] for i, s in present)
            floor = EQ_FLOOR.get(label, DEFAULT_FLOOR)
            if abs(rhs - lhs) > max(0.001 * abs(lhs), floor):
                wrong.append((code, q, label, lhs, rhs, rhs - lhs))

    # --- dual-form 보험손익 (item1 = ΣLOB bare  OR  +기타영업수익(15)-기타사업비용(16)) ---
    bo_wrong = []
    bo_hole = []
    for (code, q), d in cell.items():
        bo = d.get(1)
        lob = [d.get(2), d.get(13), d.get(14)]
        if bo is None:
            continue
        if d.get(2) is None and d.get(13) is None and d.get(14) is None:
            continue
        if any(x is None for x in lob):
            # for non-life, 자동차/일반 may legitimately be absent; for life both None is fine
            # → only HOLE if 장기(2) present but one LOB present and the other missing
            present_lob = [i for i in (2, 13, 14) if d.get(i) is not None]
            missing_lob = [i for i in (2, 13, 14) if d.get(i) is None]
            # life insurers: only item2 present, 13/14 absent → that's normal, skip
            if set(present_lob) == {2}:
                continue
            bo_hole.append((code, q, "보험손익=장기+자동차+일반", bo, present_lob, missing_lob))
            continue
        bare = sum(lob)
        cands = [bare]
        oi, oe = d.get(15), d.get(16)
        if oi is not None and oe is not None:
            cands.append(bare + oi - oe)
        diff = min((c - bo for c in cands), key=abs)
        if abs(diff) > max(0.001 * abs(bo), DEFAULT_FLOOR):
            bo_wrong.append((code, q, "보험손익(dual)", bo, bo + diff, diff))

    allwrong = sorted(wrong + bo_wrong, key=lambda t: (name_of.get(t[0], t[0]), t[1], t[2]))
    allhole = sorted(hole + bo_hole, key=lambda t: (name_of.get(t[0], t[0]), t[1], t[2]))

    print("=" * 84)
    print("WRONG — LHS & all RHS present but breakdown does NOT add up (parser bug candidate)")
    print("=" * 84)
    for code, q, label, lhs, rhs, gap in allwrong:
        print(f"  {name_of.get(code,code):14s} {q}  [{label:18s}] lhs={lhs:>12,.0f} Σ={rhs:>12,.0f} gap={gap:>+11,.0f}")
    print(f"  → WRONG = {len(allwrong)}")

    if not only_wrong:
        print()
        print("=" * 84)
        print("HOLE — LHS present, some RHS present, ≥1 RHS slice MISSING (stacked bar has a gap)")
        print("=" * 84)
        by_co = defaultdict(list)
        for code, q, label, lhs, present, missing in allhole:
            by_co[name_of.get(code, code)].append((q, label, present, missing))
        for co in sorted(by_co):
            for q, label, present, missing in sorted(by_co[co]):
                print(f"  {co:14s} {q}  [{label:18s}] present={present} missing={missing}")
        print(f"  → HOLE = {len(allhole)}")

    print()
    print(f"SUMMARY  WRONG={len(allwrong)}  HOLE={len(allhole)}")
    return 1 if allwrong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
