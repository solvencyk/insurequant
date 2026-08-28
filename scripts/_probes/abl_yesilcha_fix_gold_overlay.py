"""Fix STALE item7 gold overrides for KR0070 that assumed item6=0.

data/_gold/user_pl_cells.json carries 7 item7 overrides (2023.1Q, 2024.1Q/2Q/3Q, 2025.1Q/2Q/3Q)
from inbox/parser/20260825T1120Z (a DIFFERENT, earlier fix: item4's own 2026-08-17 override
wasn't propagating into item7's residual). Those item7 overrides were computed as
item3 - item4_override - item5 - item6, with item6 implicitly 0 (the only value item6 had at
the time). abl_yesilcha_apply_patch.py's new item6 values (2026-08-28, this ticket) make that
implicit-0 assumption stale for 5 of those 7 quarters (2024.1Q/2Q/3Q, 2025.2Q/3Q -- item6 stays
suppressed at 0 for 2023.1Q and 2025.1Q, see below, so those two overrides are still correct
as-is): build_root_masters.build_pl() applies gold overrides UNCONDITIONALLY, AFTER the fresh
pipeline value, so the override was silently clobbering the correctly-recomputed item7 in
data/dart/viz/pl_breakdown_master.json with the OLD (item6=0) number -- confirmed by
validate_master_tables.py --no-build PL_BRIDGE FAILs on exactly those 5 (company,quarter) whose
diff equals exactly the new item6 value (e.g. 2024.1Q diff=+1341.0 == item6_new).

Fix: item7_override_new = item7_override_old - item6_new (item4_override/item3/item5 unchanged
-- only item6 moved, so only its own contribution needs subtracting out of the residual).
2023.1Q's item7 override is NOT touched: item6 stays 0 there (note26 predates 2024.4Q).
2024.4Q/2025.4Q/2026.1Q/2026.2Q have no item7 override at all -- untouched, unaffected.
2025.1Q's override is ALSO not touched here even though one exists: item6 is suppressed for
that quarter too (_ABL_ITEM6_SUPPRESS_QUARTERS in tier2.py -- note37 사업비 sub-figure mismatch,
unresolved), so item6 stays 0 there and the override's item6=0 assumption is still correct.

IDEMPOTENT: this was a one-time migration, already applied (2026-08-28). Each patched entry's
`note` gets a `FOLLOW-UP 2026-08-28` marker; a re-run detects it and skips that entry rather than
subtracting item6 a second time. Kept as a reproduce/audit artifact, not meant for regular reuse.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_fix_gold_overlay.py
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

GOLD = REPO / "data/_gold/user_pl_cells.json"
MARKER = "FOLLOW-UP 2026-08-28"

TARGET_QUARTERS = ("2024.1Q", "2024.2Q", "2024.3Q", "2025.2Q", "2025.3Q")
QUARTER_DIRS = {
    "2024.1Q": "data/dart/FY2024_Q1/raw/KR0070_에이비엘생명보험",
    "2024.2Q": "data/dart/FY2024_Q2/raw/KR0070_에이비엘생명보험",
    "2024.3Q": "data/dart/FY2024_Q3/raw/KR0070_에이비엘생명보험",
    "2025.2Q": "data/dart/FY2025_Q2/raw/KR0070_에이비엘생명보험",
    "2025.3Q": "data/dart/FY2025_Q3/raw/KR0070_에이비엘생명보험",
}


def _find_xml(rel_dir):
    d = REPO / rel_dir
    xs = glob.glob(str(d / "*.xml")) + glob.glob(str(d / "xml" / "*.xml"))
    return Path(sorted(xs, key=lambda p: Path(p).stat().st_size, reverse=True)[0]) if xs else None


def _item6(q):
    xml = _find_xml(QUARTER_DIRS[q])
    tables = list(_iter_tables_with_context(xml))
    _tag_basis(tables, xml)
    return extract_tier2_abl(tables, quarter=q).get(6)


def main():
    d = json.loads(GOLD.read_text(encoding="utf-8"))
    before_bytes = GOLD.read_bytes()

    n = skipped = 0
    for e in d["set"]:
        if e.get("원보험사코드") != "KR0070" or e.get("항목번호") != 7:
            continue
        q = e["공시분기"]
        if q not in TARGET_QUARTERS:
            continue
        if MARKER in (e.get("note") or ""):
            print(f"{q}: already patched (marker found) -- skip")
            skipped += 1
            continue
        item6_new = _item6(q)
        old_override = e["값"]
        new_override = old_override - item6_new
        print(f"{q}: item7 override {old_override!r} -> {new_override!r}  (item6_new={item6_new})")
        e["값"] = new_override
        e["note"] = e["note"] + (
            f" | {MARKER} (inbox/parser/20260828T2100Z, KR0070 예실차 both legs): "
            f"this override assumed item6=0 (the only value it had at creation time). item6 is "
            f"now {item6_new:g} (note26 보험영업수익과보험영업비용-derived, note37 prose-verified) "
            f"-- subtracted out of the residual so item3=item4(override)+item5+item6+item7 still "
            f"closes: {old_override:g} - {item6_new:g} = {new_override:g}."
        )
        n += 1

    assert n + skipped == len(TARGET_QUARTERS), f"expected {len(TARGET_QUARTERS)} entries, saw {n + skipped}"
    if n == 0:
        print(f"\nnothing to do ({skipped} already patched) -- not writing")
        return

    GOLD.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\npatched {n} entries ({skipped} already-patched skipped), wrote {GOLD}")

    # sanity: file is still valid JSON with the same entry COUNT (no accidental dup/drop)
    after = json.loads(GOLD.read_text(encoding="utf-8"))
    before = json.loads(before_bytes.decode("utf-8"))
    assert len(after["set"]) == len(before["set"]), "entry count changed -- ABORT"
    print(f"entry count unchanged: {len(after['set'])}")


if __name__ == "__main__":
    main()
