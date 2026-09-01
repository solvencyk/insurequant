"""FORM_B ("item36 present, 37-40 absent"): is it a distinct mechanism?

For KR0009 / KR0150 / KR0087, using the PRE-re-conversion markdown backup:
  * which market tables does the MD actually contain (heading census)?
  * which row does extract_mkt_subs() pick item36 from?
  * where does each 위험액 현황 table live in the raw PDF, and was that page
    selected?

Hypothesis under test: FORM_B is not a third mechanism but FORM_A and/or FORM_C
landing on the sub-risk detail pages while the page carrying the 시장위험 총괄
row (which is where item36 gets picked up) survives.
"""

from __future__ import annotations

import io
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OLD_DIR = REPO / "data" / "_derived" / "md_backup_20260901_windowfix" / "md_inbox"
PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"
CODES = ["KR0009", "KR0150", "KR0087"]

ANCHORS = {
    "금리위험액현황": re.compile(r"금리위험액현황"),
    "주식위험액현황": re.compile(r"주식위험액현황"),
    "부동산위험액현황": re.compile(r"부동산위험액현황"),
    "외환위험액현황": re.compile(r"외환위험액현황"),
    "자산집중위험액현황": re.compile(r"자산집중위험액현황"),
    "시장위험액(총괄행)": re.compile(r"시장위험액"),
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    import fitz

    mkt = _load("_mkt2", REPO / "scripts" / "fill_market_subitems_to_disclosure.py")
    for code in CODES:
        mds = sorted(OLD_DIR.glob(f"{code}_*.md"))
        if not mds:
            print(f"{code}: no backup md")
            continue
        text = mds[0].read_text(encoding="utf-8")
        m = re.search(r'source_page_ranges:\s*"([^"]*)"', text)
        sel: set[int] = set()
        if m:
            for chunk in m.group(1).split(";"):
                if "-" in chunk:
                    a, _, b = chunk.partition("-")
                    sel.update(range(int(a), int(b) + 1))
        _, _, rest = text.partition("---\n")
        _, _, body = rest.partition("\n---\n")
        nbody = "".join(body.split())

        pdfs = sorted(PDF_DIR.glob(f"{code}_*.pdf"))
        doc = fitz.open(str(pdfs[0]))
        texts = ["".join((doc.load_page(i).get_text() or "").split()) for i in range(doc.page_count)]
        doc.close()

        print(f"\n=== {code} (pre-reconversion MD) ===")
        print(f"  selected pages: {sorted(sel)[:6]}...{sorted(sel)[-4:] if sel else ''}  n={len(sel)}")
        subs = mkt.extract_mkt_subs(body)
        print(f"  extract_mkt_subs -> {dict(sorted(subs.items()))}")
        for label, pat in ANCHORS.items():
            pdf_pages = [i + 1 for i, t in enumerate(texts) if pat.search(t)]
            in_md = bool(pat.search(nbody))
            inside = [p for p in pdf_pages if p in sel]
            verdict = (
                "OK" if in_md else ("FORM_C(selected,dropped)" if inside else "FORM_A(never selected)")
            )
            if not pdf_pages:
                verdict = "not in PDF"
            print(
                f"    {label:<20} pdf={str(pdf_pages)[:24]:<26} selected={str(inside)[:20]:<22}"
                f" in_md={int(in_md)}  {verdict}"
            )
        # where does the surviving item36 row live?
        for line in body.splitlines():
            if line.strip().startswith("|") and "금리위험액" in line:
                print(f"    MD row w/ 금리위험액: {line.strip()[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
