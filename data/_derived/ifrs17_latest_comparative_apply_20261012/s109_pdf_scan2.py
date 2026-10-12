"""Read-only second pass for the PDF-lineage rows that s105 could not decide (NOLABEL / NONE): linearised page text instead of y-rows.

The 경영공시 요약 포괄손익계산서 pages print  label \n v1 \n v2 \n change  (labels may span two lines: '법인세비용차감전순이익' + '(또는 ...)').
For every undecided (bucket, item) we scan ALL pages of the PDF for a label line that matches the item and read the next numeric lines; the master is compared with
v1 (current period), v2 (prior-year / comparative) and v3 at unit scales 억원 / 백만원 / 천원 / 원.  Output pdf_scan2.csv + the same report layout as s106.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
prev = list(csv.DictReader(open(HERE / "pdf_scan.csv", encoding="utf-8-sig")))
cells = {(c["code"], c["quarter"], c["pdf"]): c for c in json.load(open(HERE / "pdf_lineage_cells.json", encoding="utf-8"))}

LABELS = {
    1: [r"^보험손익$", r"^보험서비스결과$"],
    16: [r"기타사업비용"],
    17: [r"^투자손익$"],
    20: [r"^영업이익"],
    21: [r"^영업외손익$"],
    22: [r"^법인세(비용)?차감전(순)?(이익|손익)", r"^법인세차감전(순)?(이익|손익)"],
    23: [r"^법인세비용$", r"^법인세비용\(수익\)$"],
    24: [r"^(당기|분기|반기|3분기)?순이익$", r"^당기순이익$", r"^(당기|분기|반기)순이익\(손실\)$"],
}
NUMTOK = re.compile(r"^[\(\△+\-]?[0-9][0-9,]*(\.[0-9]+)?\)?$")


def norm(s):
    return re.sub(r"\s+", "", s)


def to_num(tok):
    t = tok.strip().replace(",", "").replace("+", "")
    neg = t.startswith("(") and t.endswith(")") or t.startswith("-") or t.startswith("△")
    t = t.strip("()-△")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def lin_rows(doc):
    """[(page_no, label_norm, [numeric tokens following the label line])]"""
    res = []
    for pno, page in enumerate(doc):
        lines = [l.strip() for l in page.get_text().splitlines()]
        n = len(lines)
        i = 0
        while i < n:
            lab = norm(lines[i])
            lab = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?|^[IVX]+\.|^\d+\.|^\(\d+\)", "", lab)
            lab = re.sub(r"^\((기타사업비용)\)$", r"\1", lab)
            if lab and not NUMTOK.match(lines[i]):
                j = i + 1
                # skip a second label line like '(또는 법인세비용차감전순손실)'
                if j < n and lines[j].startswith("(또는"):
                    j += 1
                toks = []
                while j < n and len(toks) < 4 and NUMTOK.match(lines[j].replace(" ", "")):
                    toks.append(lines[j].replace(" ", ""))
                    j += 1
                if toks:
                    res.append((pno + 1, lab, toks))
            i += 1
    return res


def hits_of(master, toks, item):
    vals = [to_num(t) for t in toks[:3]]
    ms = [abs(master)] if item in (16, 23) else [master]
    out = []
    for mm in ms:
        for sname, mult in (("억원", 100.0), ("백만원", 1.0), ("천원", 0.001), ("원", 1e-6)):
            for i, v in enumerate(vals):
                if v is None:
                    continue
                p = abs(v) * mult if item in (16, 23) else v * mult
                tol = 50.5 if mult == 100.0 else max(100.5 if (mm % 100 == 0 and mm != 0) else 0.51, 0.0006 * abs(p))
                if abs(p - mm) <= tol:
                    out.append(i + 1)
    return sorted(set(out))


def own_filing(pdf_rel, quarter):
    m = re.search(r"FY(\d{4})_Q(\d)", pdf_rel.replace("\\", "/"))
    return bool(m) and f"{m.group(1)}.{m.group(2)}Q" == quarter


cache = {}
out = []
for r in prev:
    if r["cls"] not in ("NOLABEL", "NONE"):
        continue
    it = int(r["item"])
    pdf = r["pdf"]
    if pdf not in cache:
        try:
            cache[pdf] = lin_rows(fitz.open(str(ROOT / pdf)))
        except Exception as e:  # noqa: BLE001
            cache[pdf] = None
    rows = cache[pdf]
    if rows is None:
        out.append({**r, "cls2": "UNREADABLE", "detail2": ""})
        continue
    pats = [re.compile(p) for p in LABELS.get(it, [])]
    cand = [(p, lab, toks) for p, lab, toks in rows if any(pt.search(lab) for pt in pats)]
    master = float(r["master"])
    best = None
    for p, lab, toks in cand:
        h = hits_of(master, toks, it)
        if h:
            best = (p, lab, toks, h)
            break
    if best:
        p, lab, toks, h = best
        out.append({**r, "cls2": "COL" + "/".join(map(str, h)), "detail2": f"p{p} {lab} {toks}"})
    elif cand:
        p, lab, toks = cand[0]
        out.append({**r, "cls2": "NONE", "detail2": f"p{p} {lab} {toks}"})
    else:
        out.append({**r, "cls2": "NOLABEL", "detail2": ""})

with open(HERE / "pdf_scan2.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print("pass-2 rows", len(out))
print(Counter((r["own"], r["cls2"]) for r in out).most_common())
print("=== own & only col>=2")
for r in out:
    if r["own"] == "True" and r["cls2"] in ("COL2", "COL3", "COL2/3"):
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["cls2"], r["detail2"][:120], "|", r["pdf"][-36:])
print("=== later & only col1")
for r in out:
    if r["own"] == "False" and r["cls2"] == "COL1":
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["cls2"], r["detail2"][:120], "|", r["pdf"][-36:])
print("=== NONE (candidate label found, no column matches)")
for r in out:
    if r["cls2"] == "NONE":
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r["own"], r["detail2"][:140])
print("NOLABEL left:", Counter(r["item"] for r in out if r["cls2"] == "NOLABEL"))
