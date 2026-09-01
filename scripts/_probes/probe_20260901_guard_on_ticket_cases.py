"""Does the new guard actually fire on the filers the inbox ticket named?

Prints page_selection_flags() for every FY2026_Q2 md_inbox file and marks the
11 companies listed in inbox 20260831T0700Z (5 body + 3 추가사례 + 3 추가사례2).
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser import quality_check as QC  # noqa: E402

TICKET = {
    "KR0049": "A 악사손해",
    "KR0095": "A 메트라이프",
    "KR0002": "A 한화손해",
    "KR0074": "A 라이나",
    "KR1000": "A 코리안리",
    "KR0009": "B 현대해상",
    "KR0150": "B 서울보증",
    "KR0087": "B 동양생명(scan)",
    "KR0001": "C 메리츠화재",
    "KR0051": "C 신한이지",
    "KR0100": "C 처브라이프",
}


def main() -> int:
    md_dir = REPO / "md_inbox" / "FY2026_Q2"
    hit = 0
    print(f"\n=== guard flags on current FY2026_Q2 MDs (pre re-conversion) ===\n")
    print(f"{'code':<9}{'ticket':<18}{'decision':<10}flags")
    print("-" * 110)
    for md in sorted(md_dir.glob("*.md")):
        meta, body = QC._read_md(md)
        code = meta.get("company_code", md.stem.split("_")[0])
        flags = QC.page_selection_flags(meta, body)
        rep = QC.score(md)
        tag = TICKET.get(code, "")
        if tag and flags:
            hit += 1
        if flags or tag:
            print(f"{code:<9}{tag:<18}{rep.decision:<10}{';'.join(flags) if flags else '-'}")
    print(f"\nticket companies flagged by the guard: {hit} / {len(TICKET)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
