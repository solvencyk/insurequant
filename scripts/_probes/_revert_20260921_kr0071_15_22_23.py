"""Revert item15/22/23 값_적용후 for KR0071 2025.2Q/2025.4Q back to their
pre-session values.

Why: fill_20260921_item14_post_backsolve.py's attempt to re-derive these three via the
R5 identity (14=15-22+23) broke two OTHER gate identities in validate_kics_disclosure.py
that don't touch item14 at all -- "적용후 mmult 불일치" (item15 must equal the R4
diversified-sqrt of items 17-20 plus item21) and "R6_item16" (item16 must equal
sum(17..21)-item15). Both use items 17-21, which this session never touched, so they
were only ever consistent with the OLD item15 -- moving item15 broke them while fixing
R5. Reverting 15/22/23 restores mmult+R6 to their prior passing state and leaves only
the (smaller, ticket-anticipated) R5 gap against the corrected item14, which needs
validation's AFTER_IDENT_ISSUER_INCONSISTENT pinning (validator territory, not parser's).

Guarded: asserts current value (the fix script's new value) before reverting.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JSON_PATH = REPO / "kics_disclosure.json"

KEY_CODE = "원보험사코드"
KEY_ITEM = "항목번호"
KEY_Q = "공시분기"
KEY_POST = "값_적용후"

REVERTS: dict[tuple[str, str, int], tuple[str, str]] = {
    ("KR0071", "2025.2Q", 15): ("16155.58", "16345.89"),
    ("KR0071", "2025.2Q", 22): ("3881.14", "3721.3"),
    ("KR0071", "2025.2Q", 23): ("6137.56", "5790.68"),
    ("KR0071", "2025.4Q", 15): ("16749.86", "16941.64"),
    ("KR0071", "2025.4Q", 22): ("4013.6", "3868.84"),
    ("KR0071", "2025.4Q", 23): ("6613.74", "6281.63"),
}


def main() -> int:
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    row_count_before = len(rows)
    index = {(r[KEY_CODE], r[KEY_Q], r[KEY_ITEM]): r for r in rows}

    mismatched = []
    for key, (expected_current, _revert_to) in REVERTS.items():
        actual = index[key].get(KEY_POST)
        if str(actual) != expected_current:
            mismatched.append((key, expected_current, actual))
    if mismatched:
        print("ABORT: guard mismatch:", mismatched)
        return 1
    print(f"guard OK: all {len(REVERTS)} cells match expected current value")

    for key, (_expected, revert_to) in REVERTS.items():
        row = index[key]
        old = row.get(KEY_POST)
        row[KEY_POST] = revert_to
        print(f"  {key}: {old} -> {revert_to} (reverted)")

    if len(rows) != row_count_before:
        print("ABORT: row count changed")
        return 1

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (unchanged count)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
