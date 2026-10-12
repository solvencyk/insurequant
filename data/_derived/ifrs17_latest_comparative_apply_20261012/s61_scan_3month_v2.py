"""Read-only systematic scan v2 (broader than s60): every DART quarterly/half-year filing XML, every statement-of-comprehensive-income table
(a row 법인세비용차감전... + a 3개월/누적 header), all Tier-1 PL items that have a statement line:
  1 보험손익|보험서비스결과|보험영업손익   15 기타영업수익   16 기타사업비용   17 투자손익|투자영업손익   20 영업이익   21 영업외손익 | 영업외수익-영업외비용
  22 법인세(비용)차감전순이익   23 법인세비용   24 (분기|반기|당기)순이익   25 기타포괄손익   31 총포괄(손)익
The numeric cells of a row (the 주석 column skipped when the header has one) are, in order, [당 3개월, 당 누적, 전 3개월, 전 누적]; the master value (abs) is compared with
each at +-0.51 (integer masters, 백만원) or +-0.0012 (fractional masters) after trying the 원/천원/백만원 scales.
Class per master cell: CUM_OK | 3M_AS_CUM | PRIOR_COL | NO_MATCH | NO_LINE.  Q1 is a control (3개월 == 누적).
Output scan3m_v2.csv
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

LINES = {
    1: [r"^보험손익$", r"^보험서비스결과$", r"^보험영업손익$"],
    15: [r"^기타영업수익$"],
    16: [r"기타사업비용$"],
    17: [r"^투자손익$", r"^투자영업손익$"],
    20: [r"^영업이익(\(손실\))?$"],
    19: [r"^(순)?보험금융손익$"],
    21: [r"^영업외손익$"],
    22: [r"법인세(비용)?차감전(계속영업)?(순)?(이익|손익)"],
    23: [r"^법인세비용(\(수익\)|\(환입\))?$", r"^법인세수익\(비용\)$"],
    24: [r"^(분기|반기|당기|3분기|계속영업분기|계속영업반기|계속영업당기)?(순이익|순손익)(\(손실\))?$", r"(분기|반기|당기)순이익", r"계속영업(분기|반기|당기)순이익"],
    25: [r"^기타포괄손익$", r"^법인세비용차감후기타포괄손익$"],
    31: [r"총포괄(손익|이익|손익\(손실\)|이익\(손실\))$"],
}


def norm(s):
    return re.sub(r"\s+", "", s or "")


def clean_label(s):
    s = norm(s)
    s = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+\.?|^[IVXlvx]+\.|^\d+\.|^\(\d+\)|^\d+\)", "", s)
    return s


def stmt_tables(xml):
    out = []
    for t in X.load_tables(str(xml)):
        labs = [clean_label(r.cells[0]) for r in t.rows if r.cells]
        if not any(re.search(r"법인세(비용)?차감전", l) for l in labs):
            continue
        hdr = "".join(norm(c) for r in t.rows[:4] for c in r.cells)
        if "3개월" not in hdr or "누적" not in hdr:
            continue
        has_note = any(norm(c) == "주석" for r in t.rows[:3] for c in r.cells)
        out.append((t, has_note))
    return out


def row_nums(r, has_note):
    cells = r.cells[1:]
    if has_note and cells:
        cells = cells[1:]
    nums = []
    for c in cells:
        v = X.printed_to_float(c)
        if v is not None:
            nums.append(v)
        elif c.strip() in ("-", "0"):
            nums.append(0.0)
    return nums


def lines_of(t, has_note):
    res = {}
    labmap = {}
    for r in t.rows:
        if not r.cells:
            continue
        lab = clean_label(r.cells[0])
        labmap.setdefault(lab, r)
        for item, pats in LINES.items():
            if item in res:
                continue
            if any(re.search(p, lab) for p in pats):
                res[item] = (row_nums(r, has_note), r.line, r.cells[0])
    if 19 not in res:
        comps = [("보험금융수익", +1), ("보험금융비용", -1), ("재보험금융수익", +1), ("재보험금융비용", -1)]
        arrs = []
        for lab, sg in comps:
            r = labmap.get(lab)
            if r is not None:
                n = row_nums(r, has_note)
                if len(n) >= 4:
                    arrs.append((sg, n[:4], r.line))
        if arrs:
            res[19] = ([sum(sg * (abs(n[i]) if sg < 0 else n[i]) for sg, n, _l in arrs) for i in range(4)], arrs[0][2], "보험금융손익(합산)")
    if 21 not in res:
        a = labmap.get("영업외수익")
        b = labmap.get("영업외비용")
        if a is not None and b is not None:
            na, nb = row_nums(a, has_note), row_nums(b, has_note)
            if len(na) == len(nb) and len(na) >= 4:
                res[21] = ([x - abs(y) for x, y in zip(na, nb)], a.line, "영업외수익-영업외비용")
    return res


def classify(m, nums):
    if m is None or len(nums) < 2:
        return None
    tol = (50.5 if (float(m).is_integer() and abs(m) >= 1000 and float(m) % 100 == 0) else 0.51) if float(m).is_integer() else 0.0012
    names4 = ("3M", "CUM", "PRIOR_3M", "PRIOR_CUM")
    for sc in (1e6, 1e3, 1.0):
        hits = [names4[i] for i, x in enumerate(nums[:4]) if abs(abs(x) / sc - abs(m)) <= tol]
        if hits:
            return "+".join(hits)
    return "NONE"


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
    sts = stmt_tables(xml)
    if not sts:
        rows.append({"code": kr, "name": names.get(kr, ""), "quarter": q, "item": "", "master": "", "cls": "NO_STATEMENT_TABLE", "xml": xml.name})
        continue
    cache = [(t, lines_of(t, hn)) for t, hn in sts]
    for item in LINES:
        m = master.get((kr, q, item))
        if m is None:
            continue
        seen = []
        for t, ln in cache:
            if item not in ln:
                continue
            nums, line, lab = ln[item]
            if len(nums) < 2:
                continue
            seen.append((classify(m, nums), line, lab, t.index, nums[:4]))
        if not seen:
            rows.append({"code": kr, "name": names.get(kr, ""), "quarter": q, "item": item, "master": m, "cls": "NO_LINE", "xml": xml.name})
            continue
        toks = [set((c or "NONE").split("+")) for c, *_ in seen]
        if any("CUM" in t for t in toks):
            fin, pick = "CUM_OK", next(x for x, t in zip(seen, toks) if "CUM" in t)
        elif any("3M" in t for t in toks):
            fin, pick = "3M_AS_CUM", next(x for x, t in zip(seen, toks) if "3M" in t)
        elif any(t & {"PRIOR_CUM", "PRIOR_3M"} for t in toks):
            fin, pick = "PRIOR_COL", next(x for x, t in zip(seen, toks) if t & {"PRIOR_CUM", "PRIOR_3M"})
        else:
            fin, pick = "NO_MATCH", seen[0]
        rows.append({"code": kr, "name": names.get(kr, ""), "quarter": q, "item": item, "master": m, "cls": fin, "line": pick[1], "label": pick[2], "table": pick[3],
                     "vals": pick[4], "xml": xml.name})

cols = ["code", "name", "quarter", "item", "master", "cls", "line", "label", "table", "vals", "xml"]
with open(HERE / "scan3m_v2.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
c = Counter((r["quarter"][5], r["cls"]) for r in rows)
for k in sorted(c):
    print(k, c[k])
for tag in ("3M_AS_CUM", "PRIOR_COL"):
    print(f"--- {tag}:")
    for r in rows:
        if r["cls"] == tag and (tag == "PRIOR_COL" or r["quarter"][5] in "23"):
            print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r.get("vals"), "L", r.get("line"), r.get("label"))
print("--- NO_MATCH (Q2/Q3):")
for r in rows:
    if r["cls"] == "NO_MATCH" and r["quarter"][5] in "23":
        print(r["code"], r["name"][:8], r["quarter"], "item", r["item"], r["master"], r.get("vals"), "L", r.get("line"), r.get("label"))
