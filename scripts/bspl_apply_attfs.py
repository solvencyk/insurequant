#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B): read the balance sheet of a financial-statement attachment PDF (text layer) into master items.  Library + CLI (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_attfs.py <pdf> [--master KRxxxx 2023.1Q]

Finds the page whose text holds 「재 무 상 태 표」 and 「자 산 총 계」, rebuilds rows with scripts/bspl_granularity/pdfrows.rows_from_page, strips the numbering
(「1.」 「(1)」 「Ⅰ.」) and maps K-IFRS labels to the master items.  Values are returned in 백만원 (unit read from the page: 원 / 천원 / 백만원).
Returns per label the [current, prior-year-end] columns.  With --master the current column is printed next to the master cells of that quarter.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity.pdfrows import rows_from_page  # noqa: E402

LABEL_ITEM = [          # (regex on the cleaned label, item)  -- order matters, first match wins
    (r"^자산총계$", 1), (r"^부채총계$", 2), (r"^자본총계$", 3),
    (r"^현금및현금성자산$", 10),
    (r"^당기손익-?공정가치측정(금융자산|유가증권)$", 11), (r"^당기손익인식(금융자산|유가증권)$", 11),
    (r"^기타포괄손익[-_]?공정가치측정(금융자산|유가증권)$", 12),
    (r"^상각후원가측정(금융자산|유가증권)$", 13),
    (r"^재보험계약자산$", 14), (r"^재보험자산$", 14),
    (r"^유형자산$", 15),
    (r"^보험계약부채$", 20), (r"^재보험계약부채$", 21), (r"^투자계약부채$", 22), (r"^차입부채$", 23), (r"^기타부채$", 24),
    (r"^자본금$", 30), (r"^기타포괄손익누계액$", 4), (r"^이익잉여금.*$", 31), (r"^결손금.*$", 31),
]


def clean(label: str) -> str:
    t = "".join(label.split())
    t = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫIVX]+\.", "", t)
    t = re.sub(r"^\d+\.", "", t)
    t = re.sub(r"^\(\d+\)", "", t)
    t = re.sub(r"\(주[^)]*\)", "", t)
    return t


def unit_of(text: str) -> float:
    m = re.search(r"\(단위\s*[:：]?\s*(원|천원|백만원|억원)\)", re.sub(r"\s+", " ", text))
    u = m.group(1) if m else None
    return {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "억원": 100.0}.get(u, None), u


def find_bs_pages(doc: fitz.Document):
    out = []
    for i in range(min(len(doc), 12)):
        tx = doc[i].get_text()
        flat = "".join(tx.split())
        if "재무상태표" in flat[:200] and "자산총계" in flat and "부채총계" in flat:
            out.append(i)
    return out


def read_bs(pdf: Path):
    """returns dict(label -> [cur, prior]) in 백만원, unit string, page numbers; rows in the order printed."""
    doc = fitz.open(str(pdf))
    pages = find_bs_pages(doc)
    if not pages:
        raise SystemExit(f"no balance-sheet page in {pdf}")
    page = pages[0]
    sc, unit = unit_of(doc[page].get_text())
    if sc is None:
        raise SystemExit(f"unit not found on page {page + 1} of {pdf}")
    rows, _free = rows_from_page(doc[page], pageno=page + 1)
    # a statement row prints [note] cur prior [prior2]: the number of period columns = the numeric tokens of the asset-total row (no note there);
    # the LAST ncols tokens of every row are the period columns (a bare dash counts as a token), the note number (single token left of them) is dropped.
    ncols = 2
    for r in rows:
        if clean(r.label) == "자산총계" and len(r.vals) >= 2:
            ncols = min(len(r.vals), 3)
            break
    out = []
    for r in rows:
        toks = list(zip(r.vals, r.dash))
        toks = toks[-ncols:] if len(toks) >= ncols else []
        vals = [v * sc if not d else 0.0 for v, d in toks]
        out.append((clean(r.label), r.label_raw, vals, [d for v, d in toks]))
    return out, unit, page + 1


def to_items(rows):
    items = {}
    for lab, raw, vals, dash in rows:
        for rx, it in LABEL_ITEM:
            if re.match(rx, lab):
                if it not in items:
                    items[it] = (raw, vals)
                break
    return items


def main():
    pdf = Path(sys.argv[1])
    rows, unit, page = read_bs(pdf)
    print(f"{pdf.name}: BS page {page}, unit {unit}")
    items = to_items(rows)
    mv = {}
    if "--master" in sys.argv:
        i = sys.argv.index("--master")
        code, q = sys.argv[i + 1], sys.argv[i + 2]
        bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
        mv = {r["항목번호"]: r["값"] for r in bs if r["원보험사코드"] == code and r["공시분기"] == q}
    for lab, raw, vals, dash in rows:
        print(f"  {raw[:44]:<46} {vals}")
    if mv:
        print("  --- items vs master")
        for it in sorted(items):
            v = items[it][1][0] if items[it][1] else None
            print(f"   item {it:>2} {items[it][0][:28]:<30} att={('-' if v is None else format(v, ',.3f')):>16}  master={mv.get(it)}")


if __name__ == "__main__":
    main()
