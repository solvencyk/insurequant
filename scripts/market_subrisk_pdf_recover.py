# -*- coding: utf-8 -*-
"""Recover 시장위험액 하위(36-40) from RAW PDF via pdfplumber when the docling MD
dropped/fragmented the breakdown table, and produce an evidence-backed census.

Supersedes the fitz line-based fill_market_subs_from_pdf for detection: pdfplumber
preserves table cell structure, so the 5-way breakdown survives even when pypdf's
flat text scrambles label/value adjacency. Handles label variants:
  '금리위험' (롯데 ③경과조치), '1.금리위험액' / 'Ⅳ.금리위험액' (삼성생명 충격시나리오방식
  중간열), fragmented one-row tables (하나손해). Value = first numeric cell after
  the label (skips a '충격시나리오 방식' method column). Reconcile-gated (<2% vs
  item19 by the 19_market M-matrix) before storing — wrong pickups never enter.

Classification per (co,q) with item19 but <5 subs:
  RECOVERED   - pdfplumber found ≥4 sub-risks that reconcile → stored
  G36_ONLY    - only 금리위험액 present (IRR table; 37-40 genuinely not broken out)
  AGGREGATE   - 시장위험액 present but NO sub-risk row anywhere in PDF (exempt candidate;
                evidence = pages scanned)
  PARTIAL_NORC- found 2-4 but doesn't reconcile (needs eyeball / variant)
  NO_PDF / SCAN - no pdf, or pdf has no text layer (image-only → OCR/gold)

Usage: PYTHONIOENCODING=utf-8 python scripts/market_subrisk_pdf_recover.py [--dry-run]
"""
from __future__ import annotations
import argparse
import json
import logging
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import pdfplumber

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from fill_market_subitems_to_disclosure import _bare_subrisk_item, _parse_value, _to_eok, mkt_est, _meta_for
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"
NAMES = {36: "3-1. 금리위험액", 37: "3-2. 주식위험액", 38: "3-3. 부동산위험액",
         39: "3-4. 외환위험액", 40: "3-5. 자산집중위험액"}


def quarter_to_period(q):
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return f"FY{m.group(1)}_Q{m.group(2)}"


def _row_value(cells):
    """first numeric cell (백만원) after col0; skips '충격시나리오 방식' method col."""
    for c in cells[1:]:
        v = _parse_value((c or "").replace("\n", " "))
        if v is not None:
            return float(v)
    return None


def extract_from_pdf(pdf_path):
    """Return ({item_no: 백만원 float}, n_pages_with_시장위험, had_text)."""
    got = {}
    n_mkt_pages = 0
    had_text = False
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if txt.strip():
                had_text = True
            if "시장위험" not in txt.replace(" ", ""):
                continue
            n_mkt_pages += 1
            for tbl in page.extract_tables():
                for row in tbl:
                    if not row or not row[0]:
                        continue
                    item = _bare_subrisk_item(row[0].replace("\n", " "))
                    if item is None or item in got:
                        continue
                    v = _row_value(row)
                    if v is not None:
                        got[item] = v
    return got, n_mkt_pages, had_text


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    item19 = {}
    have = defaultdict(set)
    name = {}
    for r in rows:
        it = int(r["항목번호"]); key = (r["원보험사코드"], r["공시분기"])
        name[r["원보험사코드"]] = r["원수사명"]
        if it == 19:
            v = _parse_value(str(r["값"]))
            if v is not None:
                item19[key] = float(v)
        if 36 <= it <= 40 and _parse_value(str(r["값"])) is not None:
            have[key].add(it)
    existing = {(r["원보험사코드"], int(r["항목번호"]), r["공시분기"]) for r in rows}

    worklist = sorted(k for k, v in item19.items() if v > 0 and len(have[k]) < 5)
    buckets = defaultdict(list)
    new_rows = []
    for code, quarter in worklist:
        pdfs = disclosure_pdfs(quarter_to_period(quarter), code)
        if not pdfs:
            buckets["NO_PDF"].append((code, quarter)); continue
        try:
            got, npg, had_text = extract_from_pdf(pdfs[0])
        except Exception as e:
            buckets["ERR"].append((code, quarter, str(e)[:40])); continue
        if not had_text:
            buckets["SCAN"].append((code, quarter)); continue
        v19 = item19[(code, quarter)]
        found = sorted(got)
        if len(found) >= 4:
            v5 = [float(_to_eok(got.get(i, 0), "백만원")) for i in (36, 37, 38, 39, 40)]
            rel = abs(mkt_est(v5) - v19) / v19 * 100
            if rel < 2:
                meta = _meta_for(rows, code)
                stored = []
                for i in (36, 37, 38, 39, 40):
                    if i in got and (code, i, quarter) not in existing:
                        new_rows.append({**meta, "원보험사코드": code, "항목번호": i,
                                         "항목명": NAMES[i], "공시분기": quarter,
                                         "값": _to_eok(got[i], "백만원")})
                        stored.append(i)
                buckets["RECOVERED"].append((code, quarter, found, round(rel, 1), stored))
                continue
            buckets["PARTIAL_NORC"].append((code, quarter, found, round(rel, 1)))
        elif found == [36] or (found and set(found) <= {36}):
            buckets["G36_ONLY"].append((code, quarter))
        elif found:
            buckets["PARTIAL_NORC"].append((code, quarter, found, None))
        else:
            buckets["AGGREGATE"].append((code, quarter, npg))

    # report
    lines = ["# 시장위험 하위 PDF recover + census", ""]
    order = ["RECOVERED", "PARTIAL_NORC", "G36_ONLY", "AGGREGATE", "SCAN", "NO_PDF", "ERR"]
    for b in order:
        items = buckets.get(b, [])
        lines.append(f"## {b}: {len(items)}")
        for it in items:
            lines.append("- " + " ".join(str(x) for x in it) + f"  ({name.get(it[0],'')})")
        lines.append("")
    out = REPO / "artifacts" / "kics_validation" / "market_subrisk_pdf_census.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    for b in order:
        print(f"  {b}: {len(buckets.get(b, []))}")
    print(f"new rows: {len(new_rows)} | report: {out}")

    if args.dry_run:
        print("(dry-run)"); return 0
    if new_rows:
        rows.extend(new_rows)
        JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
