"""Simulate the PRIORITY_KEYWORDS cap-exemption before re-converting anything.

For every PDF in the given periods, compute:
    old  = top-N by matched_count, +-window   (behaviour before this change)
    new  = old | priority pages,      +-window (behaviour after)
and report added pages, added ranges, and whether the required section anchors
(6-4 시장위험 / 금리·주식·부동산·외환·자산집중 위험액 현황 / 6-8 위험민감도) that
were OUTSIDE `old` are now INSIDE `new`.

Usage: probe_20260901_priority_selection_sim.py [FY2026_Q2 ...]
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser import docling_parser as DP  # noqa: E402

CAP = 20
WINDOW = 1
ANCHORS = (
    ("6-4_시장위험", re.compile(r"6-4\.?\s*시장위험")),
    ("금리위험액현황", re.compile(r"금리위험액\s*현황")),
    ("주식위험액현황", re.compile(r"주식위험액\s*현황")),
    ("부동산위험액현황", re.compile(r"부동산위험액\s*현황")),
    ("외환위험액현황", re.compile(r"외환위험액\s*현황")),
    ("자산집중위험액현황", re.compile(r"자산집중위험액\s*현황")),
    ("6-8_위험민감도", re.compile(r"6-8\.?\s*위험\s*민감도")),
)


def main() -> int:
    import fitz

    periods = sys.argv[1:] or ["FY2026_Q2"]
    grand = {"added_pages": 0, "closed": 0, "still_out": 0, "files": 0}
    rows = []
    for period in periods:
        pdf_dir = REPO / "data" / "disclosure" / period / "pdf"
        if not pdf_dir.is_dir():
            print(f"!! no pdf dir for {period}")
            continue
        print(f"\n=== {period} ===")
        print(f"{'code':<8}{'old':>5}{'new':>5}{'+pg':>5}{'oldR':>6}{'newR':>6}  closed / still-out")
        print("-" * 96)
        for pdf in sorted(pdf_dir.glob("*.pdf")):
            m = DP._COMPANY_PDF_STEM.match(pdf.stem)
            if not m:
                continue
            code = m.group("code")
            item = DP.PdfInput(
                company_code=code, company_dirname=pdf.stem, period=period, pdf_path=pdf
            )
            scored, total = DP._find_keyword_pages(pdf, item.keyword_terms)
            if total is None or not scored:
                continue
            ranked = sorted(scored, key=lambda x: (-x[1], x[0]))
            capped = {p for p, _, _ in ranked[:CAP]}
            forced = {p for p, _, prio in scored if prio}
            old_sel = set(DP._expand_pages(sorted(capped), total, WINDOW))
            new_sel = set(DP._expand_pages(sorted(capped | forced), total, WINDOW))
            old_r = DP._pages_to_ranges(sorted(old_sel))
            new_r = DP._pages_to_ranges(sorted(new_sel))

            doc = fitz.open(str(pdf))
            texts = ["".join((doc.load_page(i).get_text() or "").split()) for i in range(doc.page_count)]
            doc.close()
            closed, still = [], []
            for key, pat in ANCHORS:
                pages = [i + 1 for i, t in enumerate(texts) if pat.search(t)]
                if not pages:
                    continue
                if any(p in old_sel for p in pages):
                    continue  # already covered
                if any(p in new_sel for p in pages):
                    closed.append(f"{key}@{pages}")
                else:
                    still.append(f"{key}@{pages}")
            grand["files"] += 1
            grand["added_pages"] += len(new_sel - old_sel)
            grand["closed"] += len(closed)
            grand["still_out"] += len(still)
            rows.append(
                {
                    "period": period,
                    "company": code,
                    "total_pages": total,
                    "old_pages": len(old_sel),
                    "new_pages": len(new_sel),
                    "added": sorted(new_sel - old_sel),
                    "old_ranges": DP._format_ranges(old_r),
                    "new_ranges": DP._format_ranges(new_r),
                    "closed": closed,
                    "still_out": still,
                }
            )
            flag = "  " if not still else "!!"
            print(
                f"{code:<8}{len(old_sel):>5}{len(new_sel):>5}{len(new_sel - old_sel):>5}"
                f"{len(old_r):>6}{len(new_r):>6}{flag}"
                + (" ".join(closed) if closed else "-")
                + (("   STILL_OUT: " + " ".join(still)) if still else "")
            )

    print("\n== summary ==", json.dumps(grand, ensure_ascii=False))
    out = REPO / "data" / "_derived" / "_probe_priority_selection_sim.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
