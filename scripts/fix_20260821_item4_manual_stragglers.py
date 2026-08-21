"""3 item4 cells the automated label-matcher couldn't resolve (row present
in md_inbox but match_baseline_value_or_zero missed it -- not investigated
further, out of scope for this ticket), verified by direct inspection
instead:

  - KR0032 NH농협손해 2023.2Q: md_inbox/FY2023_Q2/KR0032_NH농협손해보험_amended.md
    L143 "Ⅰ. 건전성감독기준 재무상태표 상의 순자산 (1+2+3+4+5+6) | 26,049 |
    25,389 | -" (당분기=23.2Q=26,049). Cross-checked against the SAME
    company's FY2023_Q3 filing, whose own trailing column for "직전분기
    (23.2Q)" independently reads 26,049 too (L144 of that file).
  - KR0032 NH농협손해 2023.3Q: same file, L144 "24,773 | 26,049 | 25,389"
    (당분기=23.3Q=24,773; the 26,049/25,389 trailing columns cross-confirm
    the 2023.2Q fix above and 2023.1Q respectively).
  - KR0049 악사손해 2025.1Q: md_inbox/FY2025_Q1/KR0049_악사손해보험.md L273,
    plain-prose disclosure: "2025년 1분기 건전성감독기준 재무상태표상
    순자산은 4,871억원으로 전분기대비 113억원 증가했습니다." -- a narrative
    restatement of the same table figure, not a derived number.

All 3 are the standard +-1 억원-rounding signature (master already equals
sum(items5-11) exactly -- tautology fingerprint -- and differs from raw by
exactly 1).

Cell-by-cell UPSERT; prints before/after.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

FIXES = [
    ("KR0032", "2023.2Q", "26050", "26049"),
    ("KR0032", "2023.3Q", "24772", "24773"),
    ("KR0049", "2025.1Q", "4872", "4871"),
]


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    by_key = {}
    for r in rows:
        it = r.get("항목번호")
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        by_key[(r.get("원보험사코드"), r.get("공시분기"), it)] = r

    touched = []
    for code, q, expect_old, new_val in FIXES:
        row = by_key.get((code, q, 4))
        if row is None:
            print(f"  ABORT: {code} {q} item4 row not found")
            sys.exit(1)
        old = row.get("값")
        if str(old) != expect_old:
            print(f"  ABORT: {code} {q} item4 값 is {old!r}, expected {expect_old!r} "
                  f"(state drifted since this script was written)")
            sys.exit(1)
        row["값"] = new_val
        touched.append((code, q, old, new_val))
        # no 값_적용후 to re-mirror -- all three are currently None (checked
        # before writing this script)

    print(f"\ncells changed: {len(touched)}")
    for t in touched:
        print("  ", t)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(rows)} rows (row_count unchanged) -- {len(touched)} cells touched")


if __name__ == "__main__":
    main()
