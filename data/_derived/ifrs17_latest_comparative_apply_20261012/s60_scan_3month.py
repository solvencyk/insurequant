"""Read-only systematic scan: is a PL master cell the 3-MONTH amount where the YTD (cumulative) amount belongs?

Source of truth = the filing itself (data/dart/FY####_Q#/raw, same company and quarter as the master cell): every table of the XML that is a statement of
comprehensive income (a row '법인세비용차감전순이익' present, header with 3개월/누적 pairs) is read with the independent reader xmltab.py.  For each master PL
cell of quarter 2Q/3Q (and 1Q as control) with a statement line, the master value is compared at the filing unit (원/천원/백만원) with the four columns
[당 3개월, 당 누적, 전 3개월, 전 누적]; classes:
  CUM_OK        equals 당 누적 in some statement table of the filing
  3M_AS_CUM     equals 당 3개월 (and not 당 누적) in a statement table  <- the defect class
  PRIOR_COL     equals a 전기 column (wrong period)
  NO_MATCH      equals nothing (restated basis, other source, derived cell, ...)
Output scan3m_tier1.csv
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
master = {}
names = {}
for r in pl:
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
    names[r["원보험사코드"]] = r["원수사명"]

PFX = r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX\d\.\)\(\s]*"
LINES = {  # item -> list of label regexes (normalised, no spaces) ; value = signed printed amount
    1: [r"^보험손익$"],
    16: [r"기타사업비용$"],
    17: [r"^투자손익$"],
    20: [r"^영업이익(\(손실\))?$"],
    22: [r"법인세(비용)?차감전(순)?(이익|손익)(\(손실\))?$", r"법인세비용차감전순이익"],
    23: [r"^법인세비용(\(수익\))?$", r"^법인세비용\(환입\)$", r"^법인세수익\(비용\)$"],
    24: [r"^(분기|반기|당기|3분기)?(순이익|순손익)(\(손실\))?$", r"(분기|반기|당기)순이익"],
    25: [r"^기타포괄손익$"],
    31: [r"총포괄손익$", r"(분기|반기|당기)총포괄손익"],
}


def norm(s):
    return re.sub(r"\s+", "", s or "")


def clean_label(s):
    s = norm(s)
    return re.sub(PFX, "", s) if False else re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.?|^[IVX]+\.|^\d+\.|^\(\d+\)", "", s)


def stmt_tables(xml):
    out = []
    for t in X.load_tables(str(xml)):
        labs = [clean_label(r.cells[0]) for r in t.rows if r.cells]
        if not any("법인세비용차감전" in l or "법인세차감전" in l for l in labs):
            continue
        hdr = " ".join(" ".join(r.cells) for r in t.rows[:4])
        out.append((t, hdr))
    return out


def lines_of(t):
    res = {}
    for r in t.rows:
        if not r.cells or len(r.cells) < 3:
            continue
        lab = clean_label(r.cells[0])
        for item, pats in LINES.items():
            if item in res:
                continue
            if any(re.search(p, lab) for p in pats):
                vals = [X.printed_to_float(c) for c in r.cells[1:]]
                res[item] = (vals, r.line, r.cells[0])
    return res


def classify(m, vals):
    """vals = [당3M, 당누적, 전3M, 전누적] numbers in some unit; returns (class tokens joined by '+', scale).
    Tolerance in MASTER units: integer-valued masters (HTML-fallback cells are rounded 백만원 integers) +-0.51 ; fractional masters +-0.001."""
    if m is None or len(vals) < 4 or any(v is None for v in vals[:4]):
        return None, None
    tol_master = 0.51 if float(m).is_integer() else 0.0012
    for sc in (1e6, 1e3, 1.0):
        v = [abs(x) / sc for x in vals[:4]]
        hits = [k for k, x in zip(("3M", "CUM", "PRIOR_3M", "PRIOR_CUM"), v) if abs(x - abs(m)) <= tol_master]
        if hits:
            return "+".join(hits), sc
    return "NONE", None


def filings():
    for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2024.1Q", "2024.2Q", "2024.3Q", "2025.1Q", "2025.2Q", "2025.3Q", "2026.1Q", "2026.2Q"):
        d = ROOT / "data/dart" / f"FY{q[:4]}_Q{q[5]}" / "raw"
        if not d.exists():
            continue
        for cd in sorted(d.glob("KR*")):
            kr = cd.name.split("_")[0]
            xs = sorted(cd.glob("*.xml"), key=lambda p: p.stat().st_size, reverse=True)
            if xs:
                yield kr, q, xs[0]


rows = []
for kr, q, xml in filings():
    try:
        sts = stmt_tables(xml)
    except Exception as e:  # noqa: BLE001
        print("ERR", kr, q, e)
        continue
    if not sts:
        rows.append({"code": kr, "name": names.get(kr, ""), "quarter": q, "item": "", "master": "", "cls": "NO_STATEMENT_TABLE", "xml": xml.name})
        continue
    lines_cache = [(t, lines_of(t)) for t, _h in sts]
    for item in LINES:
        m = master.get((kr, q, item))
        if m is None:
            continue
        seen = []
        for t, ln in lines_cache:
            if item not in ln:
                continue
            vals, line, lab = ln[item]
            nums = [v for v in vals if v is not None]
            if len(nums) < 4:
                continue
            nums = nums[-4:]
            cls, sc = classify(m, nums)
            seen.append((cls, sc, line, lab, t.index, nums))
        if not seen:
            rows.append({"code": kr, "name": names.get(kr, ""), "quarter": q, "item": item, "master": m, "cls": "NO_LINE", "xml": xml.name})
            continue
        toks = [set((c or "NONE").split("+")) for c, *_ in seen]
        if any("CUM" in t for t in toks):
            fin = "CUM_OK"
            pick = next(x for x, t in zip(seen, toks) if "CUM" in t)
        elif any("3M" in t for t in toks):
            fin = "3M_AS_CUM"
            pick = next(x for x, t in zip(seen, toks) if "3M" in t)
        elif any(t & {"PRIOR_CUM", "PRIOR_3M"} for t in toks):
            fin = "PRIOR_COL"
            pick = next(x for x, t in zip(seen, toks) if t & {"PRIOR_CUM", "PRIOR_3M"})
        else:
            fin = "NO_MATCH"
            pick = seen[0]
        rows.append({"code": kr, "name": names.get(kr, ""), "quarter": q, "item": item, "master": m, "cls": fin, "scale": pick[1], "line": pick[2],
                     "label": pick[3], "table": pick[4], "vals": pick[5], "xml": xml.name})

cols = ["code", "name", "quarter", "item", "master", "cls", "scale", "line", "label", "table", "vals", "xml"]
with open(HERE / "scan3m_tier1.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
c = Counter((r["quarter"][5], r["cls"]) for r in rows)
for k in sorted(c):
    print(k, c[k])
print("--- 3M_AS_CUM hits in Q2/Q3 filings:")
for r in rows:
    if r["cls"] == "3M_AS_CUM" and r["quarter"][5] in "23":
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r.get("vals"), "L", r.get("line"))
print("--- PRIOR_COL hits:")
for r in rows:
    if r["cls"] == "PRIOR_COL":
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r.get("vals"), "L", r.get("line"))
