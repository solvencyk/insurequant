"""FORM_C: is the page's CONTENT really absent from the MD, or just its heading?

For each FORM_C (company, page): pull distinctive numeric tokens from the raw PDF
page with fitz, then count how many of them appear anywhere in the MD body.
Also do the same for page-1 and page+1 as controls (they prove docling did
process the surrounding pages of the same range).
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PERIOD = "FY2026_Q2"
MD_DIR = REPO / "md_inbox" / PERIOD
PDF_DIR = REPO / "data" / "disclosure" / PERIOD / "pdf"
POS = REPO / "data" / "_derived" / "_probe_formC_position.json"

# 4+ digit grouped numbers are distinctive enough to fingerprint a page.
NUM_RE = re.compile(r"\d{1,3}(?:,\d{3})+")


def _body(md: Path) -> str:
    text = md.read_text(encoding="utf-8")
    _, _, rest = text.partition("---\n")
    _, _, body = rest.partition("\n---\n")
    return body


def _page_nums(doc, pageno: int) -> set[str]:
    if pageno < 1 or pageno > doc.page_count:
        return set()
    return set(NUM_RE.findall(doc.load_page(pageno - 1).get_text() or ""))


def main() -> int:
    import fitz

    rows = json.loads(POS.read_text(encoding="utf-8"))
    md_by_code = {}
    for md in MD_DIR.glob("*.md"):
        code = md.stem.split("_")[0]
        md_by_code[code] = md

    print("\n=== FORM_C numeric fingerprint (raw page numbers found in MD) ===\n")
    print(f"{'code':<8}{'page':>5}{'n_nums':>8}{'hit':>6}{'pct':>7}   prev(p-1)      next(p+1)")
    print("-" * 92)
    out = []
    for r in rows:
        code = r["company"]
        md = md_by_code.get(code)
        if md is None:
            continue
        body = _body(md)
        pdfs = list(PDF_DIR.glob(f"{code}_*.pdf"))
        if not pdfs:
            continue
        doc = fitz.open(str(pdfs[0]))
        res = {}
        for tag, pageno in (("cur", r["page"]), ("prev", r["page"] - 1), ("next", r["page"] + 1)):
            nums = _page_nums(doc, pageno)
            hit = sum(1 for n in nums if n in body)
            res[tag] = (len(nums), hit, (hit / len(nums)) if nums else None)
        doc.close()
        c = res["cur"]
        p = res["prev"]
        n = res["next"]
        pct = f"{c[2]*100:.0f}%" if c[2] is not None else "n/a"
        ppct = f"{p[1]}/{p[0]}" if p[0] else "-/-"
        npct = f"{n[1]}/{n[0]}" if n[0] else "-/-"
        print(f"{code:<8}{r['page']:>5}{c[0]:>8}{c[1]:>6}{pct:>7}   {ppct:<14} {npct}")
        out.append({**r, "cur": c, "prev": p, "next": n})

    dest = REPO / "data" / "_derived" / "_probe_formC_fingerprint.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
