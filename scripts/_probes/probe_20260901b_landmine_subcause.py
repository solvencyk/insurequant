# -*- coding: utf-8 -*-
"""For each of the 18 landmine companies (master has 36-40 full, current MD
doesn't reproduce all 5 via extract_mkt_subs), and each MISSING item, check
whether that item's section HEADING is present anywhere in the MD body.

  HEADING_PRESENT -> the docling conversion kept the section; the failure is
                      in extract_mkt_subs()'s table-row parsing, not in page
                      selection/conversion. NOT a docling-window bug.
  HEADING_ABSENT  -> the section text is nowhere in the MD body; consistent
                      with the ticket's "whole section dropped by the
                      keyword-window" (or, if source_page_ranges also lacks
                      the expected page span, a true page-selection miss).

Read-only. No writes.
"""
from __future__ import annotations
import glob
import io
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))
import fill_market_subitems_to_disclosure as F  # noqa: E402

MD_DIR = REPO / "md_inbox" / "FY2026_Q2"

LANDMINE = {
    "KR0010": [37, 40], "KR0051": [38, 39, 40],
    "KR0068": [37, 38], "KR0079": [36, 37, 38, 39, 40],
    "KR0080": [36, 37], "KR0082": [38], "KR0087": [37, 38, 39, 40],
    "KR0094": [37, 38], "KR0099": [36, 37, 38, 40],
    "KR0104": [36, 37, 38], "KR1098": [37, 38, 39, 40],
}

RISK_NAME = {36: "금리", 37: "주식", 38: "부동산", 39: "외환", 40: "자산집중"}
# Section-heading cue: "<risk>위험액 현황" or "<risk>위험액현황" possibly with a
# leading circled-number/roman marker, OR the bare risk term itself appearing
# as a row/table header cell (e.g. "Ⅳ. 금리위험액").
def heading_present(body: str, item_no: int) -> bool:
    risk = RISK_NAME[item_no]
    pat = re.compile(rf"{risk}\s*위험\s*액\s*현황")
    return bool(pat.search(body))


def main():
    for code, missing in LANDMINE.items():
        g = sorted(glob.glob(str(MD_DIR / f"{code}_*.md")))
        if not g:
            print(f"{code}: NO_MD")
            continue
        body = Path(g[0]).read_text(encoding="utf-8")
        parts = []
        for item_no in missing:
            present = heading_present(body, item_no)
            parts.append(f"item{item_no}({RISK_NAME[item_no]})={'HEADING_PRESENT' if present else 'HEADING_ABSENT'}")
        print(f"{code}: " + " ".join(parts))


if __name__ == "__main__":
    main()
