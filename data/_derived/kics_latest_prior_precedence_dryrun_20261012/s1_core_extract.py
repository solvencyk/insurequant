"""s1_core_extract.py -- step 1 of the latest-prior-column dry run (READ-ONLY on the repo).

For every (filing period, company) PDF it reads the [경과조치 적용 전 지급여력비율 세부] table ONCE and stores the three printed
columns (cur = 해당분기, prev = 직전분기, prev2 = 전전분기) for items 1..26 (+ printed ratio row 27 is derived in master, so it is
kept separately as 'ratio_printed' when the table prints it).  Reuses the project's own extractor machinery
(scripts/detect_kics_restatement.py: table_pages / pdf_rows / map_items + VISION_ANCHORS + MANUAL_CELL_ANCHORS) so the
semantics are identical to the tool the validation stage already trusts.

usage: s1_core_extract.py [--periods FY2025_Q4,FY2026_Q1] [--codes KR0003,...] [--force]
Writes cache/core_<period>_<code>.json (one small file per filing).
"""
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
import detect_kics_restatement as det  # noqa: E402
from _disclosure_pdf_paths import latest_disclosure_pdfs  # noqa: E402

# --- recall patch (this dry run only; the project's detect_kics_restatement.py is NOT edited) -----------------------------------------
# The project extractor maps a row by substring anchors on the normalised label (Hangul+digits).  Multi-line labels whose continuation
# line sits ABOVE the numeric row come out flipped ('위험액  1. 생명장기손해보험'), so the anchor of item 17 (and 6 / 12 / 13) misses.  Add
# the flipped / doubled-text / OCR variants as extra anchors; order-consumption in map_items() is unchanged.
_EXTRA_ANCHORS = {
    6: ("이외의자본증권", "자본항목자본항목중중보통주"),
    12: ("불인정하는항목",),
    13: ("재분류하는항목",),
    17: ("위험액1생명장기손해보험", "생명장기손액보험위험액", "장기손해보험생명", "1생명장기손해보험"),
}
det.ANCHORS = [(it, tuple(aa) + _EXTRA_ANCHORS.get(it, ())) for it, aa in det.ANCHORS]


def two_col_rows(page, cols=None):
    """det.pdf_rows() for a table with two numeric column clusters: pad a dummy third cluster to the right of them."""
    if cols is None:
        words = page.get_text("words")
        xs = sorted((w[0] + w[2]) / 2 for w in words if det.NUM_RE.match(w[4]))
        if len(xs) < 14:
            return [], None
        cl = []
        for x in xs:
            if cl and x - cl[-1][-1] <= 12:
                cl[-1].append(x)
            else:
                cl.append([x])
        cl = [c for c in cl if len(c) >= 8]
        if len(cl) >= 2:
            cols = cl[-2:] + [[max(cl[-1]) + 70.0]]
        else:
            # FY2023_Q1 prints ONE numeric column only (22.4Q / 22.3Q are em dashes) and det.pdf_rows() keeps only lines with >= 2 numbers,
            # so those 38 filings stay NO_GRID: no own-filing control for 2023.1Q blocks (documented, not worked around)
            return [], None
    return det.pdf_rows(page, cols)


def gapfill_by_order(rows, mapped):
    """The table's row order is fixed by the supervisory form.  A numeric row that stays unmapped between two mapped items is assigned to the
    single missing item number between them -- only when exactly ONE row and exactly ONE candidate item are in the gap (otherwise untouched)."""
    # identify which row object each mapped item came from (vals lists are shared by identity)
    pos = {}
    for k, row in enumerate(rows):
        for it, v in mapped.items():
            if row[1] is v:
                pos[it] = k
    n = 0
    filled = []
    items_sorted = sorted(pos)
    for a, b in zip(items_sorted, items_sorted[1:]):
        ka, kb = pos[a], pos[b]
        between_rows = [k for k in range(ka + 1, kb)]
        missing_items = [it for it in range(a + 1, b) if it not in mapped and it not in (10, 24, 25, 26, 27)]
        if len(between_rows) == 1 and len(missing_items) == 1:
            mapped[missing_items[0]] = rows[between_rows[0]][1]
            filled.append(missing_items[0])
            n += 1
    return mapped, filled


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def extract_filing(period: str, code: str):
    """-> dict(status, pdf, pages, cols={'cur':{item:[val,dec]}, 'prev':..., 'prev2':...}, unmatched, manual)"""
    out = {"period": period, "code": code, "status": None, "pdf": None, "pages": None, "cols": {}, "unmatched": [], "method": None, "err": None}
    pdfs = latest_disclosure_pdfs(period, code)
    if not pdfs:
        out["status"] = "NO_PDF"
        out["err"] = f"{period} has no PDF for {code}"
        return out
    p = pdfs[0]
    out["pdf"] = p.relative_to(REPO).as_posix()
    out["n_pdfs_same_filing"] = len(pdfs)
    # vision anchors (project-recorded, eyeballed) take precedence exactly as det.extract does
    va = {col: det.VISION_ANCHORS.get((period, code, col)) for col in ("cur", "prev")}
    import fitz
    try:
        doc = fitz.open(p)
    except Exception as e:  # noqa: BLE001
        out["status"] = "OPEN_FAIL"
        out["err"] = f"{type(e).__name__}: {e}"
        return out
    try:
        pages = det.table_pages(doc)
        if not pages:
            out["status"] = "NO_TEXT_TABLE"
            out["err"] = "no text-layer 3-column table found (scan PDF or heading variant)"
            out["page_count"] = doc.page_count
            for col, v in va.items():
                if v:
                    out["cols"][col] = {str(k): [float(x), 0] for k, x in v.items() if isinstance(k, int) and isinstance(x, (int, float))}
                    out["method"] = "vision"
            if out["cols"]:
                out["status"] = "VISION_ONLY"
            return out
        rows, cols = [], None
        for pno in pages:
            r, cols = det.pdf_rows(doc[pno], cols)
            rows.extend(r)
        if not rows:
            # FY2023_Q1 / Q2 filings print only TWO numeric columns (the third, 22.4Q / 22.3Q, is an em dash: K-ICS did not exist before 2023).
            # The project extractor needs three column clusters; pad a dummy third one so cur / prev are read and prev2 stays empty.
            cols2 = None
            for pno in pages:
                r, cols2 = two_col_rows(doc[pno], cols2)
                rows.extend(r)
            if rows:
                out["layout"] = "two_numeric_columns(third=em dash)"
        if not rows:
            out["status"] = "NO_GRID"
            out["err"] = "table page found but no numeric grid"
            return out
        mapped, _labels, unmatched = det.map_items(rows)
        mapped, filled = gapfill_by_order(rows, mapped)
        out["gapfill"] = len(filled)
        out["gapfill_items"] = filled
        out["unmatched"] = unmatched[:12]
        out["pages"] = [x + 1 for x in pages]
        out["method"] = "pdf_text"
        for col, idx in (("cur", 0), ("prev", 1), ("prev2", 2)):
            d = {}
            for it, v in mapped.items():
                val, dec = v[idx]
                d[str(it)] = [val, dec]
            # MANUAL anchors for cells the coordinate extractor misses (only cur/prev exist in the project tool)
            if col in ("cur", "prev"):
                for it in range(1, 28):
                    if d.get(str(it), [None, 0])[0] is None:
                        hit = det.MANUAL_CELL_ANCHORS.get((period, code, col, it))
                        if hit:
                            d[str(it)] = [float(hit[0]), 0]
            if va.get(col):
                d = {str(k): [float(x), 0] for k, x in va[col].items() if isinstance(k, int) and isinstance(x, (int, float))}
                out["method"] = "pdf_text+vision"
            out["cols"][col] = d
        out["status"] = "OK"
    except Exception as e:  # noqa: BLE001
        out["status"] = "ERROR"
        out["err"] = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-400:]}"
    finally:
        doc.close()
    return out


def main():
    periods = [x for x in (arg("--periods", "") or "").split(",") if x] or sorted(p.name for p in DISC.iterdir() if re.match(r"FY\d{4}_Q\d$", p.name))
    rows = read_rows()
    codes_all = sorted({r["원보험사코드"] for r in rows})
    codes = [x for x in (arg("--codes", "") or "").split(",") if x] or codes_all
    force = "--force" in sys.argv
    CACHE.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    n = 0
    for period in periods:
        for code in codes:
            f = CACHE / f"core_{period}_{code}.json"
            if f.exists() and not force:
                continue
            t1 = time.time()
            res = extract_filing(period, code)
            write_json_lf(f, res)
            n += 1
            print(f"{period} {code} {res['status']:14s} {time.time()-t1:5.1f}s pages={res.get('pages')} {('| ' + str(res.get('err'))[:80]) if res.get('err') else ''}", flush=True)
    print(f"done: {n} extracted in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
