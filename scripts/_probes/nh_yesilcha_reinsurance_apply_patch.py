"""Apply the verified NH농협손해보험(KR0032) 재보험 예실차(item11) values as a CELL-LEVEL patch
to data/dart/viz/pl_breakdown_master.json, then propagate to root PL_breakdown.json via
build_root_masters.build_pl() (the individual function, NOT main() -- main() is destructive on
this git-purged branch, see CLAUDE.md).

Ticket: inbox/parser/20260828T1900Z__orchestrator__KR0032__reinsurance_yesilcha_item11.md
Companion boundary probe: scripts/_probes/nh_yesilcha_reinsurance_boundary_probe.py
Handler: scripts.pl_breakdown.companies.extract_tier2_nh / _nh_gmm_re_incurred

For each of the 11 quarters where the (5) reinsurance rollforward note exists
(2023.4Q-2026.2Q), computes item11 via the (already-patched, verified) handler and item12 as
the closure residual (item8 - item9 - item10 - item11), then upserts BOTH cells' 값 in-place
in the master (2023.2Q/2023.3Q are intentionally left untouched -- the source note doesn't
exist there, matching item6's own precedent).

Does NOT touch any other item/company/quarter. Prints a full before/after diff and asserts the
item8=item9+item10+item11+item12 closure holds for every KR0032 quarter both before and after.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(REPO))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.companies import extract_tier2_nh

MASTER = REPO / "data" / "dart" / "viz" / "pl_breakdown_master.json"

RAW = {
    "2023.4Q": REPO / "data/dart/FY2023_Q4/raw/KR0032_NH농협손해보험_20240329001662/20240329001662.xml",
    "2024.1Q": REPO / "data/dart/FY2024_Q1/raw/KR0032_NH농협손해보험/20240514001436.xml",
    "2024.2Q": REPO / "data/dart/FY2024_Q2/raw/KR0032_NH농협손해보험/20240814001448.xml",
    "2024.3Q": REPO / "data/dart/FY2024_Q3/raw/KR0032_NH농협손해보험/20241114001354.xml",
    "2024.4Q": REPO / "data/dart/FY2024_Q4/raw/KR0032_NH농협손해보험_20250331003247/20250331003247.xml",
    "2025.1Q": REPO / "data/dart/FY2025_Q1/raw/KR0032_NH농협손해보험/20250515001078.xml",
    "2025.2Q": REPO / "data/dart/FY2025_Q2/raw/KR0032_NH농협손해보험/20250814001701.xml",
    "2025.3Q": REPO / "data/dart/FY2025_Q3/raw/KR0032_NH농협손해보험/20251114001790.xml",
    "2025.4Q": REPO / "data/dart/FY2025_Q4/raw/KR0032_NH농협손해보험_20260331004099/20260331004099.xml",
    "2026.1Q": REPO / "data/dart/FY2026_Q1/raw/KR0032_NH농협손해보험/20260529001870.xml",
    "2026.2Q": REPO / "data/dart/FY2026_Q2/raw/KR0032_NH농협손해보험/20260814003298.xml",
}


def main():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}

    # --- pre-patch closure audit (all KR0032 quarters with item8/9/10/11/12 rows) ----------
    by_q = {}
    for r in rows:
        if r["원보험사코드"] != "KR0032" or r["항목번호"] not in (8, 9, 10, 11, 12):
            continue
        by_q.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
    print("=== PRE-PATCH closure audit (item8 == item9+item10+item11+item12) ===")
    for q in sorted(by_q):
        v = by_q[q]
        if None in (v.get(8), v.get(9), v.get(10), v.get(11), v.get(12)):
            print(f"  {q}: incomplete row set {v} -- skip")
            continue
        lhs, rhs = v[8], v[9] + v[10] + v[11] + v[12]
        ok = abs(lhs - rhs) < 1
        print(f"  {q}: item8={lhs:,.0f}  sum9-12={rhs:,.0f}  {'OK' if ok else 'MISMATCH!!'}")
        assert ok, f"pre-patch closure broken at {q}"

    # --- compute item11 via the (patched) handler, patch item11+item12 ----------------------
    changes = []
    for q, path in RAW.items():
        tables = list(_iter_tables_with_context(path))
        out = extract_tier2_nh(tables)
        i11_new = out.get(11)
        if i11_new is None:
            print(f"  {q}: handler returned no item11 -- SKIP (not filling)")
            continue
        k11 = ("KR0032", 11, q)
        k12 = ("KR0032", 12, q)
        if k11 not in idx or k12 not in idx:
            print(f"  {q}: item11/item12 row missing from master -- SKIP")
            continue
        r11, r12 = idx[k11], idx[k12]
        i8, i9, i10 = by_q[q][8], by_q[q][9], by_q[q][10]
        i11_old, i12_old = r11["값"], r12["값"]
        i12_new = i8 - i9 - i10 - i11_new
        changes.append((q, i11_old, i11_new, i12_old, i12_new))
        r11["값"] = i11_new
        r12["값"] = i12_new

    print("\n=== CHANGES (item11, item12) ===")
    print(f"{'quarter':8s} {'item11_old':>11s} {'item11_new':>11s}  {'item12_old':>11s} {'item12_new':>11s}")
    for q, i11o, i11n, i12o, i12n in changes:
        print(f"{q:8s} {i11o:>11,.0f} {i11n:>11,.0f}  {i12o:>11,.0f} {i12n:>11,.0f}")
    print(f"\n{len(changes)} quarters patched, {len(changes) * 2} cells changed")

    # --- post-patch closure re-audit ---------------------------------------------------------
    by_q2 = {}
    for r in rows:
        if r["원보험사코드"] != "KR0032" or r["항목번호"] not in (8, 9, 10, 11, 12):
            continue
        by_q2.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
    print("\n=== POST-PATCH closure audit ===")
    for q in sorted(by_q2):
        v = by_q2[q]
        if None in (v.get(8), v.get(9), v.get(10), v.get(11), v.get(12)):
            print(f"  {q}: incomplete row set {v} -- skip")
            continue
        lhs, rhs = v[8], v[9] + v[10] + v[11] + v[12]
        ok = abs(lhs - rhs) < 1
        print(f"  {q}: item8={lhs:,.0f}  sum9-12={rhs:,.0f}  {'OK' if ok else 'MISMATCH!!'}")
        assert ok, f"post-patch closure broken at {q}"

    # indent=1 matches build_pl_breakdown.py's own writer (scripts/build_pl_breakdown.py:670) --
    # using indent=2 here would reformat all 11546 rows and bury the real 22-cell diff.
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nWrote {MASTER}")


if __name__ == "__main__":
    main()
