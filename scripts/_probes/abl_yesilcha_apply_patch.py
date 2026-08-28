"""Surgical patch for inbox/parser/20260828T2100Z__orchestrator__KR0070__abl_yesilcha_both_legs.md.

Self-contained -- calls the REAL, updated scripts/pl_breakdown/tier2.py::extract_tier2_abl
(item6/item11 via _abl_note26_yesilcha, verified against the note37 prose cross-check and the
item3/item8 independent-source cross-check; see abl_yesilcha_full_probe.py for that population
verification) directly on each quarter's freshly-parsed raw tables, then applies the results as
cell-level updates to data/dart/viz/pl_breakdown_master.json for KR0070 ONLY:

  - item6 (원수 예실차): set 값 where the handler produced a value (None for 2024.4Q and 2025.1Q,
    by design -- see _ABL_ITEM6_SUPPRESS_QUARTERS in tier2.py); item7 (기타, residual) recomputed as
    item3 - item4 - item5 - item6_new (mirrors build_pl_breakdown.assemble()'s own branch
    EXACTLY -- item3/4/5 are untouched, already-trusted values read from the CURRENT master,
    not recomputed from raw).
  - item11 (재보험 예실차): set 값 where the handler produced a value; item12 (기타, residual)
    recomputed as item8 - item9 - item10 - item11_new ONLY when item9 AND item10 are BOTH
    already non-null this quarter (matches assemble()'s exact guard -- when item9/10 are None,
    item12 stays whatever it already was, i.e. null, unchanged).
  - No other cell, company, or row is touched. A full company-code census before/after confirms
    the changed-key set is exactly {KR0070} x {6,7,11,12} x <the target quarters>.

This is a JSON-level PATCH, not a build_pl_breakdown.py rerun (forbidden on this branch --
data/dart/FY2023-2024 raw for OTHER companies was git-purged; a full rerun would collapse
those masters). scripts/build_root_masters.py::build_pl() (individual call, NOT main()) must be
run separately afterward to propagate 값/값_당분기 into the root PL_breakdown.json, and
data/_gold/user_pl_cells.json's item7 overrides for 2024.1-3Q/2025.1-3Q need
abl_yesilcha_fix_gold_overlay.py (they predate this fix and assumed item6=0 -- build_pl()
UPSERTS them unconditionally, AFTER this patch, so left alone they silently reintroduce the old
item6=0 assumption into the propagated item7). Then sync_master_xlsx_sheet.py "손익분해PL".

Re-running this script after the patch is already applied is a safe no-op (old==new, "0 cells
changed").

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_apply_patch.py
"""
import glob
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _tag_basis
from scripts.pl_breakdown.tier2 import extract_tier2_abl

MASTER = REPO / "data/dart/viz/pl_breakdown_master.json"
CODE = "KR0070"

QUARTER_DIRS = {
    "2023.1Q": "data/dart/FY2023_Q1/raw/KR0070_에이비엘생명보험",
    "2023.2Q": "data/dart/FY2023_Q2/raw/KR0070_에이비엘생명보험",
    "2023.3Q": "data/dart/FY2023_Q3/raw/KR0070_에이비엘생명보험",
    "2023.4Q": "data/dart/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518",
    "2024.1Q": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험",
    "2024.2Q": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험",
    "2024.3Q": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험",
    "2024.4Q": "data/dart/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358",
    "2025.1Q": "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험",
    "2025.2Q": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험",
    "2025.3Q": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험",
    "2025.4Q": "data/dart/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080",
    "2026.1Q": "data/dart/FY2026_Q1/raw/KR0070_에이비엘생명보험",
    "2026.2Q": "data/dart/FY2026_Q2/raw/KR0070_에이비엘생명보험",
}


def _find_xml(rel_dir):
    d = REPO / rel_dir
    xs = glob.glob(str(d / "*.xml")) + glob.glob(str(d / "xml" / "*.xml"))
    if not xs:
        return None
    return Path(sorted(xs, key=lambda p: Path(p).stat().st_size, reverse=True)[0])


def _compute_handler_output():
    out = {}
    for q, rel_dir in QUARTER_DIRS.items():
        xml = _find_xml(rel_dir)
        if xml is None:
            continue
        tables = list(_iter_tables_with_context(xml))
        _tag_basis(tables, xml)
        out[q] = extract_tier2_abl(tables, quarter=q)
    return out


def main():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    handler_out = _compute_handler_output()

    # index KR0070 rows by (item, quarter) -> row dict (mutated in place)
    idx = {}
    for r in rows:
        if r["원보험사코드"] == CODE:
            idx[(r["항목번호"], r["공시분기"])] = r

    # pre-patch snapshot for the combo-diff (whole file, all companies)
    before = json.loads(json.dumps(rows))  # deep copy via round-trip

    changed = []
    for q, t2 in handler_out.items():
        item6 = t2.get(6)
        item11 = t2.get(11)

        if item6 is not None:
            v3 = idx[(3, q)]["값"]
            v4 = idx[(4, q)]["값"]
            v5 = idx[(5, q)]["값"]
            if None not in (v3, v4, v5):
                old6 = idx[(6, q)]["값"]
                new6 = float(item6)
                new7 = v3 - v4 - v5 - new6
                old7 = idx[(7, q)]["값"]
                idx[(6, q)]["값"] = new6
                idx[(7, q)]["값"] = new7
                changed.append((q, 6, old6, new6))
                changed.append((q, 7, old7, new7))

        if item11 is not None:
            v8 = idx[(8, q)]["값"]
            v9 = idx[(9, q)]["값"]
            v10 = idx[(10, q)]["값"]
            old11 = idx[(11, q)]["값"]
            new11 = float(item11)
            idx[(11, q)]["값"] = new11
            changed.append((q, 11, old11, new11))
            if None not in (v8, v9, v10):
                old12 = idx[(12, q)]["값"]
                new12 = v8 - v9 - v10 - new11
                idx[(12, q)]["값"] = new12
                changed.append((q, 12, old12, new12))
            # else: item12 stays whatever it already was (None) -- item9/10 not both present.

    print(f"{'quarter':8s} {'item':>4s} {'old':>14s} {'new':>14s}")
    for q, item, old, new in changed:
        oldf = f"{old:,.2f}" if isinstance(old, (int, float)) else str(old)
        newf = f"{new:,.2f}" if isinstance(new, (int, float)) else str(new)
        print(f"{q:8s} {item:>4d} {oldf:>14s} {newf:>14s}")
    print(f"\n{len(changed)} cells changed")

    # ---- combo-diff: confirm ONLY KR0070 item6/7/11/12 rows changed --------- #
    before_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in before}
    after_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in rows}
    assert set(before_idx) == set(after_idx), "row set changed -- ABORT (should never happen, in-place mutation only)"
    diff_keys = [k for k in before_idx if before_idx[k] != after_idx[k]]
    companies = {k[0] for k in diff_keys}
    items = {k[1] for k in diff_keys}
    print(f"\ncombo-diff: {len(diff_keys)} (code,item,quarter) keys changed")
    print(f"  companies touched: {sorted(companies)}")
    print(f"  items touched: {sorted(items)}")
    if companies != {CODE} or not items.issubset({6, 7, 11, 12}):
        print("  !!! UNEXPECTED SCOPE -- NOT WRITING FILE !!!")
        sys.exit(1)
    print(f"  row count before={len(before)} after={len(rows)} (must match): {'OK' if len(before)==len(rows) else 'MISMATCH'}")

    # indent=1 matches build_pl_breakdown.py's own OUT.write_text(...) call (scripts/
    # build_pl_breakdown.py:670) -- indent=2 here would reformat every one of the file's
    # 11,546 rows for a whitespace-only reason, turning a 33-cell patch into a full-file diff.
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {MASTER}")


if __name__ == "__main__":
    main()
