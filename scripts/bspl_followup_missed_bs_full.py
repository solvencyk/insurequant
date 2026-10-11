#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 5: Stage-A misses.

Stage A starts an 8-1 statement only on a page whose compact text contains '재무상태표'.  KR1098 2026.2Q prints the heading as
'8-1. 재무상태' (no 표), so its 8-1 balance sheet was never extracted.  This lists every (company, quarter) whose Stage-A file has NO
bs_full table but whose PDF has a page carrying all three totals (자산총계 / 부채총계 / 자본총계), i.e. a statement page the
classifier missed.  Read-only (PDF text only).  Output: data/_derived/bspl_followup_20261011/missed_bs_full.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)          # 'unknown cid font type' spam of broken-font PDFs

from bspl_granularity.tables import comp  # noqa: E402

TABLES = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "tables"
OUT = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "missed_bs_full.json"


def main():
    res = []
    n_scan = 0
    for p in sorted(TABLES.glob("KR*_20??.?Q.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if any(t["kind"] == "bs_full" for t in d.get("tables", [])):
            continue
        pdf = ROOT / d["pdf"] if d.get("pdf") else None
        if not pdf or not pdf.exists():
            continue
        n_scan += 1
        doc = fitz.open(pdf)
        hits = []
        try:
            for i in range(len(doc)):
                c = comp(doc[i].get_text())
                if all(x in c for x in ("자산총계", "부채총계", "자본총계")) and "요약재무상태표" not in c and "건전성감독기준" not in c:
                    hits.append({"page": i + 1, "has_8-1": ("8-1" in c), "has_재무상태": ("재무상태" in c),
                                 "pointer": ("첨부" in c and "참조" in c)})
        finally:
            doc.close()
        if hits:
            code, q = p.stem.split("_")
            res.append({"code": code, "quarter": q, "pdf": d["pdf"], "pages": hits})
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"Stage-A docs without bs_full scanned: {n_scan}; with a missed statement page: {len(res)}")
    for r in res:
        print(r["code"], r["quarter"], [(h["page"], "8-1" if h["has_8-1"] else "", "ptr" if h["pointer"] else "") for h in r["pages"]][:6])


if __name__ == "__main__":
    main()
