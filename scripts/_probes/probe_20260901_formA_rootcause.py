"""FORM_A root cause: is it the keyword LIST, the top-N CAP, or the WINDOW width?

For every FY2026_Q2 PDF, re-run _find_keyword_pages with the CURRENT keyword list
and, for each anchor page that the census marked FORM_A, report:
    score        = matched_count on that page (0 => keyword list gap)
    rank         = position in the (-score, page) ranking (>cap => cap eviction)
    cap          = item.max_keyword_hit_pages default (20)
    would_select = is the page inside the +-window expansion of the top-cap pages?

Verdict per anchor page:
    KEYWORD_LIST  score == 0 and no neighbour hit reaches it
    CAP_EVICTION  score >= 1 (a genuine hit) but rank > cap
    WINDOW_GAP    score == 0 but a neighbour within +-2 is a hit (wider window fixes)
    FIXED_NOW     already inside the selection with the current keyword list
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from solvency.parser import docling_parser as DP  # noqa: E402

PERIOD = "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / PERIOD / "pdf"
CENSUS = REPO / "data" / "_derived" / "_probe_docling_3forms_census.json"
CAP = 20
WINDOW = 1


def main() -> int:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    out_rows = []
    tally: dict[str, int] = {}
    print(f"\n=== FORM_A root cause ({PERIOD}) — cap={CAP} window={WINDOW} ===\n")
    for r in census:
        code = r.get("company")
        if r.get("error"):
            continue
        bad_pages: dict[int, list[str]] = {}
        for key, a in r["anchors"].items():
            if a["verdict"] != "FORM_A":
                continue
            for p in a["pdf_pages"]:
                bad_pages.setdefault(p, []).append(key)
        if not bad_pages:
            continue
        pdf = PDF_DIR / f"{r['dirname']}.pdf"
        item = DP.PdfInput(
            company_code=code, company_dirname=pdf.stem, period=PERIOD, pdf_path=pdf
        )
        scored, total = DP._find_keyword_pages(pdf, item.keyword_terms)
        score_by_page = {p: s for p, s in scored}
        ranked = sorted(scored, key=lambda x: (-x[1], x[0]))
        rank_by_page = {p: i + 1 for i, (p, _) in enumerate(ranked)}
        top_pages = sorted(p for p, _ in ranked[:CAP])
        selected = set(DP._expand_pages(top_pages, total or 0, WINDOW))
        # what if the cap were lifted entirely?
        sel_nocap = set(DP._expand_pages(sorted(p for p, _ in ranked), total or 0, WINDOW))

        for p in sorted(bad_pages):
            sc = score_by_page.get(p, 0)
            rk = rank_by_page.get(p)
            if p in selected:
                verdict = "FIXED_NOW"
            elif sc >= 1 and rk is not None and rk > CAP:
                verdict = "CAP_EVICTION"
            elif p in sel_nocap:
                verdict = "CAP_EVICTION"
            elif sc == 0 and any(
                (p + d) in score_by_page for d in (-2, 2)
            ):
                verdict = "WINDOW_GAP"
            else:
                verdict = "KEYWORD_LIST"
            tally[verdict] = tally.get(verdict, 0) + 1
            out_rows.append(
                {
                    "company": code,
                    "page": p,
                    "anchors": bad_pages[p],
                    "score": sc,
                    "rank": rk,
                    "n_candidates": len(scored),
                    "verdict": verdict,
                }
            )
            print(
                f"  {code:<8} p{p:<4} score={sc:<3} rank={str(rk):<5}"
                f" cand={len(scored):<4} {verdict:<14} {','.join(bad_pages[p])}"
            )

    print("\nverdict tally:", json.dumps(tally, ensure_ascii=False))
    out = REPO / "data" / "_derived" / "_probe_formA_rootcause.json"
    out.write_text(json.dumps(out_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
