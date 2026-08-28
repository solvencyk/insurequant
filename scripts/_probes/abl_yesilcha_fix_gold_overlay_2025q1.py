"""Fix the STALE 2025.1Q item7 gold override for KR0070 that assumed item6=0.

Follow-up to abl_yesilcha_fix_gold_overlay.py (2026-08-28), which fixed 5 of 7 item7
overrides (2024.1Q/2Q/3Q, 2025.2Q/3Q) but explicitly left 2025.1Q's alone because item6 was
STILL suppressed for that quarter at the time (_ABL_ITEM6_SUPPRESS_QUARTERS in tier2.py).
inbox/parser/20260829T1100Z__orchestrator__KR0070__fill_2024q4_2025q1_yesilcha.md now fills
item6 for 2025.1Q (= -3,591 백만원, note26-derived, note37 prose-verified once the
발생사고요소조정/기타사업비용 "outside the 4-item boundary" rows are accounted for), so the same
stale-assumption bug now applies to this override too: it was computed as
item3 - item4_override(20,087) - item5 - item6, with item6 implicitly 0.

Fix: item7_override_new = item7_override_old - item6_new (item3/item4_override/item5
unchanged -- only item6 moved). Verified against a from-scratch recompute using item4's
OWN override value (20,087, not PL_SRC's raw pre-override 22,447):
    17,198.63 - 20,087.00 - 3,059.00 - (-3,591.00) = -2,356.37
    old_override - item6_new = -5,947.37 - (-3,591.00) = -2,356.37   (same answer, both ways)

2024.4Q has NO item7 override in this file (confirmed by census) -- nothing to do there; its
item7 was recomputed directly in pl_breakdown_master.json by abl_yesilcha_apply_patch.py.

IDEMPOTENT: safe to re-run -- a MARKER in the note is checked first.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_yesilcha_fix_gold_overlay_2025q1.py
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
MARKER = "FOLLOW-UP 2026-08-29"
TARGET_QUARTER = "2025.1Q"
QUARTER_XML_DIR = REPO / "data/dart/FY2025_Q1/raw/KR0070_에이비엘생명보험"


def _find_xml(d):
    xs = glob.glob(str(d / "*.xml")) + glob.glob(str(d / "xml" / "*.xml"))
    return Path(sorted(xs, key=lambda p: Path(p).stat().st_size, reverse=True)[0]) if xs else None


def _item6(q):
    xml = _find_xml(QUARTER_XML_DIR)
    tables = list(_iter_tables_with_context(xml))
    _tag_basis(tables, xml)
    return extract_tier2_abl(tables, quarter=q).get(6)


def main():
    d = json.loads(GOLD.read_text(encoding="utf-8"))
    before_bytes = GOLD.read_bytes()

    target = [e for e in d["set"]
              if e.get("원보험사코드") == "KR0070" and e.get("항목번호") == 7
              and e.get("공시분기") == TARGET_QUARTER]
    assert len(target) == 1, f"expected exactly 1 matching entry, found {len(target)}"
    e = target[0]

    if MARKER in (e.get("note") or ""):
        print(f"{TARGET_QUARTER}: already patched (marker found) -- nothing to do")
        return

    item6_new = _item6(TARGET_QUARTER)
    assert item6_new is not None, "handler returned None for item6 -- ABORT (suppress set not cleared?)"
    old_override = e["값"]
    new_override = old_override - item6_new
    print(f"{TARGET_QUARTER}: item7 override {old_override!r} -> {new_override!r}  (item6_new={item6_new})")

    e["값"] = new_override
    e["note"] = e["note"] + (
        f" | {MARKER} (inbox/parser/20260829T1100Z, KR0070 2024Q4/2025Q1 예실차): "
        f"this override assumed item6=0 (still suppressed as of the 2026-08-28 fix pass). "
        f"item6 is now {item6_new:g} (note26-derived, note37 prose-verified once "
        f"발생사고요소조정/기타사업비용 outside-4-item-boundary rows are added back) -- subtracted "
        f"out of the residual so item3=item4(override)+item5+item6+item7 still closes: "
        f"{old_override:g} - {item6_new:g} = {new_override:g}."
    )

    GOLD.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {GOLD}")

    after = json.loads(GOLD.read_text(encoding="utf-8"))
    before = json.loads(before_bytes.decode("utf-8"))
    assert len(after["set"]) == len(before["set"]), "entry count changed -- ABORT"
    print(f"entry count unchanged: {len(after['set'])}")


if __name__ == "__main__":
    main()
