"""What is special about the pages docling bad_allocs on?

Compares page geometry / image / drawing counts for the pages recorded in
``docling_dropped_pages`` against the rest of the same document.
"""

from __future__ import annotations

import io
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"


def main() -> int:
    import fitz

    print(f"\n{'code':<8}{'page':>6}{'drop':>6}{'w x h':>16}{'imgs':>6}{'draws':>7}{'chars':>7}")
    print("-" * 60)
    for md in sorted(MD_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        m = re.search(r'docling_dropped_pages:\s*"([^"]*)"', text)
        if not m or not m.group(1).strip():
            continue
        dropped = {int(x) for x in m.group(1).split(",") if x.strip().isdigit()}
        code = md.stem.split("_")[0]
        pdfs = sorted(PDF_DIR.glob(f"{code}_*.pdf"))
        if not pdfs:
            continue
        doc = fitz.open(str(pdfs[0]))
        stats = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            rect = page.rect
            stats.append(
                (
                    i + 1,
                    i + 1 in dropped,
                    round(rect.width),
                    round(rect.height),
                    len(page.get_images(full=True)),
                    len(page.get_drawings()),
                    len(page.get_text() or ""),
                )
            )
        doc.close()
        for pno, drop, w, h, imgs, draws, chars in stats:
            if drop or pno <= 2:
                print(
                    f"{code:<8}{pno:>6}{('YES' if drop else '-'):>6}"
                    f"{f'{w}x{h}':>16}{imgs:>6}{draws:>7}{chars:>7}"
                )
        d = [s for s in stats if s[1]]
        k = [s for s in stats if not s[1]]
        if d and k:
            print(
                f"  {code} means -> dropped: imgs={statistics.mean(x[4] for x in d):.1f}"
                f" draws={statistics.mean(x[5] for x in d):.0f}"
                f" | kept: imgs={statistics.mean(x[4] for x in k):.1f}"
                f" draws={statistics.mean(x[5] for x in k):.0f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
