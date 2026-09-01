"""Are the 2026.2Q items 29-35 gaps real absences or another window drop?

For each company missing items 29-35 in the master:
  * print item17 (생명장기손해보험위험액) — 0 means the children cannot exist
  * scan the raw PDF with fitz for the 생명장기 sub-risk table anchors
  * report whether those pages are inside the MD's source_page_ranges
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

QUARTER = "2026.2Q"
PERIOD = "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / PERIOD / "pdf"
MD_DIR = REPO / "md_inbox" / PERIOD

ANCHORS = (
    ("사망위험액", re.compile(r"사망위험액")),
    ("장수위험액", re.compile(r"장수위험액")),
    ("해지위험액", re.compile(r"해지위험액")),
    ("대재해위험액", re.compile(r"대재해위험액")),
    ("생명장기위험액현황", re.compile(r"생명.{0,4}장기.{0,10}위험액.{0,4}현황")),
)


def main() -> int:
    import fitz

    master = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    keys = list(master[0].keys())
    F = {"code": keys[0], "item": keys[4], "quarter": keys[6], "val": keys[7]}
    cells: dict[tuple[str, int], str] = {}
    companies = set()
    for r in master:
        if r.get(F["quarter"]) != QUARTER:
            continue
        companies.add(r[F["code"]])
        try:
            cells[(r[F["code"]], int(r[F["item"]]))] = r.get(F["val"])
        except (TypeError, ValueError):
            pass

    missing = sorted(
        c for c in companies if any((c, i) not in cells or cells.get((c, i)) in (None, "", "None") for i in range(29, 36))
    )
    print(f"\n=== 2026.2Q items 29-35 gaps ({len(missing)} companies) ===\n")
    for code in missing:
        item17 = cells.get((code, 17))
        gaps = [i for i in range(29, 36) if cells.get((code, i)) in (None, "", "None")]
        pdfs = sorted(PDF_DIR.glob(f"{code}_*.pdf"))
        anchor_hits = {}
        density = 0.0
        sel: set[int] = set()
        if pdfs:
            doc = fitz.open(str(pdfs[0]))
            texts = ["".join((doc.load_page(i).get_text() or "").split()) for i in range(doc.page_count)]
            doc.close()
            density = sum(len(t) for t in texts) / max(1, len(texts))
            for label, pat in ANCHORS:
                pages = [i + 1 for i, t in enumerate(texts) if pat.search(t)]
                if pages:
                    anchor_hits[label] = pages
            mds = sorted(MD_DIR.glob(f"{code}_*.md"))
            if mds:
                text = mds[0].read_text(encoding="utf-8")
                m = re.search(r'source_page_ranges:\s*"([^"]*)"', text)
                if m:
                    for chunk in m.group(1).split(";"):
                        if "-" in chunk:
                            a, _, b = chunk.partition("-")
                            sel.update(range(int(a), int(b) + 1))
        inside = {k: [p for p in v if p in sel] for k, v in anchor_hits.items()}
        print(f"{code}  item17={item17!r}  gaps={gaps}  pdf_density={density:.0f}")
        for label, pages in anchor_hits.items():
            print(f"     {label:<20} pdf_pages={pages}  in_selected={inside[label]}")
        if not anchor_hits:
            print("     (no 생명장기 sub-risk anchor found in raw PDF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
