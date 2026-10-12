"""Read-only: verify the PDF-lineage Tier-1 PL cells (how=disclosure_summary_pl) against the printed 경영공시 PDF pages.

For every bucket in pdf_lineage_cells.json and every item of the bucket, locate the label row on the PDF (PyMuPDF words grouped by y), read the numeric
tokens right of the label in order ([current, prior-year, change] in the 요약 table; audited statements print [current, prior] or [3M, cumulative, ...]),
and classify the master value (백만원) against the first four numeric tokens at unit scales x100 (억원), x1 (백만원), x0.001 (천원->백만원) and x1e-6 (원->백만원):
   COL1 / COL2 / COL3 / COL4 / NONE / NOLABEL.     COL1 = the first printed number (current period)
A master equal to COL2 would mean the prior-year column was loaded; COL3/COL4 in a 4-column table would be the 3-month-vs-cumulative family.
Output pdf_scan.csv + summary.   usage: s105_pdf_scan.py   (about a minute)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
cells = json.loads((HERE / "pdf_lineage_cells.json").read_text(encoding="utf-8"))

LABELS = {
    1: [r"^보험손익$", r"^보험서비스결과$", r"^\(?보험손익\)?$"],
    16: [r"기타사업비용"],
    17: [r"^투자손익$", r"^투자영업손익$"],
    20: [r"^영업이익(\(또는영업손실\)|\(손실\))?$"],
    21: [r"^영업외손익$"],
    22: [r"^법인세(비용)?차감전(순)?(이익|손익)(\(또는법인세비용차감전순손실\)|\(손실\))?$"],
    23: [r"^법인세비용$"],
    24: [r"^(당기|분기|반기|3분기)?순이익(\(또는당기순손실\)|\(손실\))?$", r"^당기순이익$"],
}
NUM = re.compile(r"^\(?-?[0-9][0-9,]*(\.[0-9]+)?\)?$")


def norm(s):
    return re.sub(r"\s+", "", s)


def to_num(tok):
    t = tok.replace(",", "")
    neg = t.startswith("(") and t.endswith(")") or t.startswith("-")
    t = t.strip("()-")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def rows_of(page):
    words = page.get_text("words")  # x0, y0, x1, y1, word, block, line, wno
    rows = []
    for w in sorted(words, key=lambda w: ((w[1] + w[3]) / 2, w[0])):
        yc = (w[1] + w[3]) / 2
        if rows and abs(rows[-1][0] - yc) <= 3.2:
            rows[-1][1].append(w)
        else:
            rows.append([yc, [w]])
    return [(yc, sorted(ws, key=lambda w: w[0])) for yc, ws in rows]


ROWCACHE = {}


def all_rows(doc, key):
    """[(page_no, label_text, [numeric tokens right of the label])] for every row of the PDF that has a label and at least one number (cached per file)"""
    if key in ROWCACHE:
        return ROWCACHE[key]
    res = []
    for pno, page in enumerate(doc):
        for yc, ws in rows_of(page):
            lab_words, nums = [], []
            seen_num = False
            for w in ws:
                tk = w[4]
                if NUM.match(tk):
                    nums.append(tk)
                    seen_num = True
                elif not seen_num:
                    lab_words.append(tk)
            lab = norm("".join(lab_words))
            lab = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?|^[IVX]+\.|^\d+\.|^\(\d+\)", "", lab)
            if lab and nums:
                res.append((pno + 1, lab, nums))
    ROWCACHE[key] = res
    return res


def find_rows(doc, item, key):
    pats = [re.compile(p) for p in LABELS[item]]
    for pno, lab, nums in all_rows(doc, key):
        if any(p.search(lab) for p in pats):
            yield pno, lab, nums


def own_filing(pdf_rel, quarter):
    m = re.search(r"FY(\d{4})_Q(\d)", pdf_rel.replace("\\", "/"))
    return bool(m) and f"{m.group(1)}.{m.group(2)}Q" == quarter


def classify(master, nums):
    vals = [to_num(t) for t in nums[:4]]
    hits = []
    for scale_name, mult in (("억원", 100.0), ("백만원", 1.0), ("천원", 0.001), ("원", 1e-6)):
        for i, v in enumerate(vals):
            if v is None:
                continue
            printed_m = v * mult
            tol = (100.5 if float(master) % 100 == 0 and float(master) != 0 else 0.51) if True else 0.51
            tol = max(tol, 0.0006 * abs(printed_m)) if mult != 100.0 else 50.5
            if abs(printed_m - master) <= tol:
                hits.append((i + 1, scale_name))
    return hits


out = []
cache = {}
for b in cells:
    pdf = ROOT / b["pdf"]
    if not pdf.exists():
        out.append({**{k: b[k] for k in ("code", "name", "quarter")}, "item": "", "master": "", "cls": "NO_PDF", "detail": b["pdf"]})
        continue
    if pdf not in cache:
        try:
            cache[pdf] = fitz.open(str(pdf))
        except Exception as e:  # noqa: BLE001
            cache[pdf] = None
    doc = cache[pdf]
    if doc is None:
        out.append({**{k: b[k] for k in ("code", "name", "quarter")}, "item": "", "master": "", "cls": "PDF_UNREADABLE", "detail": b["pdf"]})
        continue
    for it in b["items"]:
        m = b["values"].get(str(it)) if str(it) in b["values"] else b["values"].get(it)
        if m is None or it not in LABELS:
            continue
        found = list(find_rows(doc, it, str(pdf)))
        if not found:
            out.append({"code": b["code"], "name": b["name"], "quarter": b["quarter"], "item": it, "master": m, "cls": "NOLABEL", "detail": "", "pdf": b["pdf"], "own": own_filing(b["pdf"], b["quarter"])})
            continue
        best = None
        for pno, lab, nums in found:
            hits = classify(abs(m) if it in (16, 23) else m, nums)
            hits2 = classify(abs(m), nums) if not hits else hits
            if hits2:
                best = (pno, lab, nums[:4], hits2)
                break
        if best is None:
            pno, lab, nums = found[0]
            out.append({"code": b["code"], "name": b["name"], "quarter": b["quarter"], "item": it, "master": m, "cls": "NONE", "detail": f"p{pno} {lab} {nums[:4]}", "pdf": b["pdf"], "own": own_filing(b["pdf"], b["quarter"])})
        else:
            pno, lab, nums, hits = best
            cols = sorted({h[0] for h in hits})
            out.append({"code": b["code"], "name": b["name"], "quarter": b["quarter"], "item": it, "master": m, "cls": "COL" + "/".join(map(str, cols)), "detail": f"p{pno} {lab} {nums}", "pdf": b["pdf"], "own": own_filing(b["pdf"], b["quarter"])})

with open(HERE / "pdf_scan.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["code", "name", "quarter", "item", "master", "cls", "detail", "pdf", "own"], restval="")
    w.writeheader()
    w.writerows(out)
print("rows", len(out))
print(Counter(r["cls"] for r in out).most_common())
print("--- not COL1:")
for r in out:
    if r["cls"] not in ("COL1", "NOLABEL", "COL1/2", "COL1/3", "COL1/4"):
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["cls"], r["detail"][:120])
