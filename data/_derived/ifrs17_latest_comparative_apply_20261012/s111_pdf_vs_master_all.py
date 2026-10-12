"""Read-only independent cross-check of the Tier-1 PL master against the OWN-filing 경영공시 PDF (요약 포괄손익계산서, 억원, cumulative 'current period' column)
for EVERY company/quarter 2023.1Q-2026.2Q that has a PDF, items 16 (기타사업비용), 22 (세전이익), 23 (법인세), 24 (당기순이익) [+ 1, 17, 20, 21 for information].

Why: the DART-XML scan (s61) only sees companies/quarters with a statement table; 기타사업비용 is not on that statement; PDF-lineage cells need the printed column.
The PDF summary prints  [current period (cumulative), same period of the prior year, change]  so a 3-month column or a prior-year column shows up as a mismatch here.
A mismatch is |master - 100*printed| > max(150 백만원, 1.5 % of |master|) (basis differences 감독회계 vs 재무제표 and 억원 rounding explain smaller gaps).
Output pdf_vs_master.csv   usage: s111_pdf_vs_master_all.py
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
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in pl}
NAMES = {r["원보험사코드"]: r["원수사명"] for r in pl}

LABELS = {
    1: [r"^보험손익$"],
    16: [r"기타사업비용"],
    17: [r"^투자손익$"],
    20: [r"^영업이익"],
    21: [r"^영업외손익$"],
    22: [r"^법인세(비용)?차감전(순)?(이익|손익)"],
    23: [r"^법인세비용$"],
    24: [r"^(당기|분기|반기|3분기)?순이익", r"^당기순이익"],
}
NUMTOK = re.compile(r"^[\(\△+\-]?[0-9][0-9,]*(\.[0-9]+)?\)?$")


def norm(s):
    return re.sub(r"\s+", "", s)


def to_num(tok):
    t = tok.strip().replace(",", "").replace("+", "").replace(" ", "")
    neg = (t.startswith("(") and t.endswith(")")) or t.startswith("-") or t.startswith("△")
    t = t.strip("()-△")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def lin_rows(doc, maxpages=12):
    """first `maxpages` pages only (the summary table is on pages 3-6); [(page, label, [tokens])]"""
    res = []
    for pno, page in enumerate(doc):
        if pno >= maxpages:
            break
        lines = [l.strip() for l in page.get_text().splitlines()]
        n = len(lines)
        for i in range(n):
            if not lines[i] or NUMTOK.match(lines[i].replace(" ", "")):
                continue
            lab = norm(lines[i])
            lab = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?|^[IVX]+\.|^\d+\.|^\(\d+\)", "", lab)
            lab = re.sub(r"^\((기타사업비용)\)$", r"\1", lab)
            j = i + 1
            if j < n and lines[j].startswith("(또는"):
                j += 1
            toks = []
            while j < n and len(toks) < 3 and NUMTOK.match(lines[j].replace(" ", "")):
                toks.append(lines[j].replace(" ", ""))
                j += 1
            if toks:
                res.append((pno + 1, lab, toks))
    return res


out = []
nopdf = 0
quarters = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
for q in quarters:
    fy = f"FY{q[:4]}_Q{q[5]}"
    d = ROOT / "data/disclosure" / fy / "raw"
    if not d.exists():
        continue
    for pdf in sorted(d.glob("KR*.pdf")):
        code = pdf.name.split("_")[0]
        if code not in NAMES:
            continue
        try:
            doc = fitz.open(str(pdf))
        except Exception:
            out.append({"code": code, "name": NAMES[code], "quarter": q, "item": "", "master": "", "printed_cur": "", "diff": "", "cls": "PDF_UNREADABLE", "detail": pdf.name})
            continue
        rows = lin_rows(doc)
        doc.close()
        for it, pats in LABELS.items():
            m = M.get((code, q, it))
            if m is None:
                continue
            cp = [re.compile(p) for p in pats]
            cand = [(p, lab, toks) for p, lab, toks in rows if any(c.search(lab) for c in cp)]
            if not cand:
                out.append({"code": code, "name": NAMES[code], "quarter": q, "item": it, "master": m, "printed_cur": "", "diff": "", "cls": "NOLABEL", "detail": pdf.name})
                continue
            p, lab, toks = cand[0]
            cur = to_num(toks[0])
            if cur is None:
                out.append({"code": code, "name": NAMES[code], "quarter": q, "item": it, "master": m, "printed_cur": toks[0], "diff": "", "cls": "UNPARSED", "detail": f"p{p} {lab} {toks}"})
                continue
            printed_m = cur * 100.0
            ma = abs(m) if it in (16, 23) else m
            pa = abs(printed_m) if it in (16, 23) else printed_m
            diff = ma - pa
            tol = max(150.0, 0.015 * abs(ma))
            cls = "MATCH" if abs(diff) <= tol else "MISMATCH"
            out.append({"code": code, "name": NAMES[code], "quarter": q, "item": it, "master": m, "printed_cur": toks[0], "diff": round(diff, 1), "cls": cls, "detail": f"p{p} {lab} {toks} | {pdf.name}"})

cols = ["code", "name", "quarter", "item", "master", "printed_cur", "diff", "cls", "detail"]
with open(HERE / "pdf_vs_master.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(out)
print("rows", len(out))
print(Counter((r["item"], r["cls"]) for r in out if r["item"] in (16, 22, 23, 24)).most_common(30))
print("--- MISMATCH items 16/22/23/24:")
for r in out:
    if r["cls"] == "MISMATCH" and r["item"] in (16, 22, 23, 24):
        print(r["code"], r["name"][:7], r["quarter"], "item", r["item"], "master", r["master"], "printed", r["printed_cur"], "diff", r["diff"], "|", r["detail"][:100])
