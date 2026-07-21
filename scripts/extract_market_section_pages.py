# -*- coding: utf-8 -*-
"""Phase 0 of the 시장위험 36-46 recovery: localize the market-risk section pages
in each gap (co,q)'s disclosure PDF and dump their text + table rows to a small
per-(co,q) markdown artifact, so the recovery Workflow agents read ~15 localized
pages instead of a 700-page PDF.

Large life-insurer 4Q filings (한화생명 740p, 동양생명 642p) do NOT have a single
5-row 시장위험 decomposition table. The 5 sub-risk amounts live in SEPARATE per-risk
'현황' sections (②금리위험액 현황 / 주식위험액 현황 / …), each on its own page with
a different table shape, plus a 순자산가치 (IRR scenario) row for items 41-46. This
script finds those pages by text signal and dumps them; an LLM agent then reads the
amounts (layout varies too much for one regex), and a sqrt(V'MV)≈item19 reconcile
gate verifies before anything is stored.

Parallel (ProcessPool) with a hard per-PDF timeout so one huge PDF can't hang the
batch (the monolith hung 56 min on one). Read-only: writes artifacts only, never
kics_disclosure.json.

Usage:
  python scripts/extract_market_section_pages.py --workers 8 --timeout 180 [--only KR0082:2024.4Q,...]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import warnings
import logging
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FTimeout
from pathlib import Path

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

JSON_PATH = REPO / "kics_disclosure.json"
DISCLOSURE = REPO / "data" / "disclosure"
OUTDIR = REPO / "artifacts" / "kics_validation" / "market_pages"

# page-localization signal: a per-risk 현황 section, the 5-way list, the IRR table,
# or the bare 시장위험액 line.
_PAGE_SIGNAL = re.compile(
    r"시장위험액"
    r"|(금리|주식|부동산|외환|자산집중)\s*위험액?\s*현황"
    r"|순자산가치"
    r"|주식위험.{0,6}부동산위험.{0,6}외환위험"
)
# rows worth keeping from a page's tables
_ROW_KEEP = re.compile(r"위험액?|순자산가치|충격|익스포져|시장위험|금리|주식|부동산|외환|자산집중")


def _parse_value(raw):
    if raw is None:
        return None
    s = str(raw).replace(",", "").strip()
    for ch in ("△", "▲", "▽", "▼", "−", "(", ")"):
        s = s.replace(ch, "-" if ch in "△▲▽▼−" else "")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    return float(s)


def quarter_to_period(q):
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return f"FY{m.group(1)}_Q{m.group(2)}"


def _keep_table_rows(rows):
    """Filter table rows to ones carrying a risk label or a number."""
    out = []
    for row in rows:
        cells = [(c or "").replace("\n", " ").strip() for c in row]
        if any(_ROW_KEEP.search(c) for c in cells) or any(
            _parse_value(c) is not None for c in cells
        ):
            out.append(" | ".join(cells))
    return out


def _emit_localized(code, quarter, npages, kept, had_text):
    if not had_text:
        return (code, quarter, "SCAN", 0, False)
    if not kept:
        return (code, quarter, "NO_SIGNAL", 0, True)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / f"{code}_{quarter}.md").write_text(
        f"# {code} {quarter} — market-risk section pages ({npages}p total)\n\n"
        + "\n\n".join(kept),
        encoding="utf-8",
    )
    return (code, quarter, "OK", len(kept), True)


def _localize_fitz(code, quarter, pdf_path):
    """Fallback backend: PyMuPDF (fitz) reads PDFs whose xref pdfplumber/pdfminer
    chokes on (Unexpected EOF). find_tables() also yields cleaner rows than
    pdfplumber's extract_tables on these filings. Mirrors localize_and_dump output."""
    import fitz
    kept, had_text = [], False
    doc = fitz.open(pdf_path)
    npages = doc.page_count
    for i in range(npages):
        page = doc[i]
        txt = page.get_text() or ""
        if txt.strip():
            had_text = True
        if not _PAGE_SIGNAL.search(txt.replace(" ", "")):
            continue
        block = [f"### page {i}", txt.strip()]
        try:
            tables = page.find_tables().tables
        except Exception:
            tables = []
        for ti, tbl in enumerate(tables):
            try:
                rows = _keep_table_rows(tbl.extract())
            except Exception:
                rows = []
            if rows:
                block.append(f"[table {ti}]")
                block.extend(rows)
        kept.append("\n".join(block))
        if len(kept) >= 30:
            break
    doc.close()
    return _emit_localized(code, quarter, npages, kept, had_text)


def localize_and_dump(args):
    """Worker: returns (code, quarter, status, n_pages_kept, had_text).

    Primary backend = pdfplumber. On any open/parse failure (e.g. pdfminer
    `Unexpected EOF` on a malformed xref), fall back to fitz so the (co,quarter)
    is NOT silently dropped to ERR — these PDFs are intact, only the backend
    chokes. (root-cause of the 2026-06-14 NH/DB손해 무음 누락.)"""
    code, quarter, pdf_path = args
    try:
        import pdfplumber
        kept = []
        had_text = False
        with pdfplumber.open(pdf_path) as pdf:
            npages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    had_text = True
                if not _PAGE_SIGNAL.search(txt.replace(" ", "")):
                    continue
                block = [f"### page {i}", txt.strip()]
                for ti, tbl in enumerate(page.extract_tables() or []):
                    rows = _keep_table_rows(tbl)
                    if rows:
                        block.append(f"[table {ti}]")
                        block.extend(rows)
                kept.append("\n".join(block))
                if len(kept) >= 30:
                    break
    except Exception:
        # pdfplumber/pdfminer choked (malformed xref etc.) — fitz reads it fine.
        return _localize_fitz(code, quarter, pdf_path)
    return _emit_localized(code, quarter, npages, kept, had_text)


def build_worklist(only=None):
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    item19, have, name = {}, defaultdict(set), {}
    for r in rows:
        it = int(r["항목번호"]); key = (r["원보험사코드"], r["공시분기"])
        name[r["원보험사코드"]] = r["원수사명"]
        if it == 19 and _parse_value(r["값"]) is not None:
            item19[key] = _parse_value(r["값"])
        if 36 <= it <= 40 and _parse_value(r["값"]) is not None:
            have[key].add(it)
    work = sorted(k for k, v in item19.items() if v and v > 0 and len(have[k]) < 5)
    if only:
        sel = {tuple(s.split(":")) for s in only.split(",")}
        work = [k for k in work if k in sel]
    targets = []
    for code, quarter in work:
        pdfs = sorted(glob.glob(str(DISCLOSURE / quarter_to_period(quarter) / "raw" / f"{code}_*.pdf")))
        if pdfs:
            targets.append((code, quarter, pdfs[0]))
    return targets, item19, name


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--only", default=None, help="comma list CODE:QUARTER to restrict")
    args = ap.parse_args(argv)

    targets, item19, name = build_worklist(args.only)
    print(f"targets={len(targets)} workers={args.workers} timeout={args.timeout}s", flush=True)
    buckets = defaultdict(list)
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(localize_and_dump, t): (t[0], t[1]) for t in targets}
        for f, key in list(fut.items()):
            try:
                code, quarter, status, npg, _ = f.result(timeout=args.timeout)
                buckets[status].append((code, quarter, npg))
            except FTimeout:
                buckets["TIMEOUT"].append((key[0], key[1], 0))
            except Exception as e:
                buckets["ERR"].append((key[0], key[1], str(e)[:50]))
            done += 1
            if done % 25 == 0:
                print(f"  ...{done}/{len(targets)}", flush=True)
        ex.shutdown(wait=False, cancel_futures=True)

    print("\n=== Phase 0 localization ===")
    for b in ("OK", "NO_SIGNAL", "SCAN", "TIMEOUT", "ERR"):
        items = buckets.get(b, [])
        print(f"  {b}: {len(items)}")
    # index file for the workflow
    idx = {f"{c}:{q}": {"item19_eok": item19[(c, q)], "name": name.get(c, ""),
                        "file": f"artifacts/kics_validation/market_pages/{c}_{q}.md"}
           for c, q, _ in buckets.get("OK", [])}
    (OUTDIR.parent / "market_pages_index.json").write_text(
        json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    # also dump non-OK lists for the EXEMPT/scan follow-up
    nonok = {b: [[c, q] for c, q, *_ in buckets.get(b, [])] for b in ("NO_SIGNAL", "SCAN", "TIMEOUT", "ERR")}
    (OUTDIR.parent / "market_pages_nonok.json").write_text(
        json.dumps(nonok, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nindexed OK: {len(idx)} -> artifacts/kics_validation/market_pages_index.json")


if __name__ == "__main__":
    main(sys.argv[1:])
