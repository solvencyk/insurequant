# -*- coding: utf-8 -*-
"""KR0104 2023.4Q neighbour check (READ-ONLY): master 2023.4Q cumulative vs the FY2024 annual report prior-year column and the FY2023 annual current column."""
import json
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
L = {(r["공시분기"], r["항목번호"]): r for r in live if r["원보험사코드"] == "KR0104"}
out, res = [], {}


def num(s):
    s = s.strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    v = float(s)
    return -v if neg else v


def find_xml(pattern):
    d = sorted((ROOT / "data/dart").glob(pattern))
    assert len(d) == 1, d
    x = [f for f in sorted(d[0].glob("*.xml")) if "_" not in f.stem]
    assert len(x) == 1, x
    return x[0]


def rows_of(path, title_pat="4-2. 포괄손익계산서"):
    ls = path.read_text(encoding="utf-8").split("\n")
    st = [i for i, l in enumerate(ls) if "<TITLE" in l and title_pat in l]
    out_ = []
    # take the LAST matching title = separate statement section 4 if several
    a = st[-1]
    b = next(i for i in range(a + 1, len(ls)) if "<TITLE" in ls[i])
    cur = None
    rows = []
    for i in range(a, b):
        l = ls[i]
        if l.startswith("<TR"):
            cur = []
        elif l.startswith("</TR>"):
            if cur:
                rows.append(cur)
            cur = None
        elif cur is not None:
            m = re.match(r"<P[^>]*>(.*)</P>", l)
            if m:
                cur.append((i + 1, m.group(1).strip().replace("\u3000", "").replace(" ", "")))
    unit = [t for i in range(a, min(a + 400, b)) for t in re.findall(r"<P[^>]*>(.*)</P>", ls[i]) if "단위" in t]
    return a + 1, b, rows, unit, st


def pick(rows, labels):
    for lab in labels:
        key = lab.replace(" ", "")
        hits = [r for r in rows if r and r[0][1] == key]
        if hits:
            r = hits[0]
            n = [(ln, t) for ln, t in r[1:] if num(t) is not None]
            return lab, len(hits), n
    return None, 0, []


LAB = {1: ["보험손익"], 16: ["기타사업비용"], 17: ["투자손익"], 20: ["영업이익(손실)", "영업이익"], 21: ["영업외손익"], 22: ["법인세차감전순이익"],
       23: ["법인세비용(수익)", "법인세비용"], 24: ["당기순이익", "당기순이익(손실)"], 25: ["기타포괄손익"], 26: ["기타포괄손익-공정가치측정금융자산관련손익"],
       27: ["보험계약자산(부채)순금융손익"], 28: ["현금흐름위험회피파생상품평가손익"], 29: ["기타포괄손익-공정가치측정금융자산평가손익"],
       30: ["재보험계약자산(부채)순금융손익"], 31: ["총포괄손익"]}
FA = find_xml("FY2024_Q4/raw/KR0104_*")
FO = find_xml("FY2023_Q4/raw/KR0104_*")
for tag, path in (("FY2024_annual", FA), ("FY2023_annual", FO)):
    a, b, rows, unit, st = rows_of(path)
    out.append("%s %s statement lines %d-%d unit=%s titles=%s" % (tag, path.name, a, b, unit, st))
    res[tag] = {"file": str(path.relative_to(ROOT)).replace("\\", "/"), "unit": unit, "stmt_lines": [a, b], "items": {}}
    hdr = [t for r in rows[:6] for _, t in r if not re.fullmatch(r"[\d,().-]+", t)][:12]
    out.append("   header-ish texts: %s" % hdr)
    for it, labs in LAB.items():
        lab, cnt, n = pick(rows, labs)
        out.append("   i%2d label=%s hits=%d numeric cells=%s" % (it, lab, cnt, [(ln, t) for ln, t in n]))
        res[tag]["items"][str(it)] = {"label": lab, "hits": cnt, "cells": n}
(HERE / "KR0104_verify4q.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
(HERE / "KR0104_verify4q.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("ok")
