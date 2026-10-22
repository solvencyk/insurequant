"""Read-only. Read the SEPARATE-basis comprehensive income statement of KR0005 from the raw DART XMLs (current and prior columns, YTD and 3-month)
with raw line numbers, and derive Tier-1 items with the production definitions (fetch_dart_fs._parse / assemble)."""
from KR0005_common import *
import json, re

def stmt_rows(fy):
    p = main_xml(fy)
    L = P.read_lines(p)
    lo, hi = P.sections(L)["sep_fs"]
    rows = P.rows_in_range(L, lo, hi)
    out, on = [], False
    for r in rows:
        if not r["cells"]:
            continue
        lab = r["cells"][0][0].replace("\u3000", "").replace(" ", "")
        if lab == "포괄손익계산서" and not on:
            on = True
            continue
        if not on:
            continue
        out.append({"tr": r["tr"], "lab": lab, "cells": [(num(t), ln, t) for t, ln in r["cells"][1:]]})
        if lab.endswith("총포괄손익"):
            break
    return rel(p), out

def pick(rows, pat, nth=0):
    hits = [r for r in rows if re.fullmatch(pat, r["lab"])]
    return hits[nth] if len(hits) > nth else None

def derive(rows, col):
    """return {item: (value_in_won?? no: 백만원), cites}"""
    it, ct = {}, {}
    def val(r):
        if r is None or col is None or col >= len(r["cells"]):
            return None, None
        v, ln, t = r["cells"][col]
        return v, ln
    def put(k, r, name=None):
        v, ln = val(r)
        it[k] = v; ct[k] = [(r["lab"] if r else name, ln)]
    put(1, pick(rows, r"Ⅰ\.(보험손익|보험서비스결과)"))
    put(16, pick(rows, r"\(3\)기타사업비용"))
    put(17, pick(rows, r"Ⅱ\.투자손익"))
    r_ii = pick(rows, r"\(1\)보험금융수익"); r_ri = pick(rows, r"\(2\)재보험금융수익")
    r_ie = pick(rows, r"\(1\)보험금융비용"); r_re = pick(rows, r"\(2\)재보험금융비용")
    vs = [val(r) for r in (r_ii, r_ri, r_ie, r_re)]
    f = lambda x: 0.0 if x[0] is None else x[0]
    it[19] = f(vs[0]) - f(vs[2]) + f(vs[1]) - f(vs[3])
    ct[19] = [(n, v[1]) for n, v in zip(("보험금융수익", "재보험금융수익", "보험금융비용", "재보험금융비용"), vs)]
    it["19_parts"] = [v[0] for v in vs]
    if it[17] is not None:
        it[18] = it[17] - it[19]
    put(20, pick(rows, r"Ⅲ\.영업이익"))
    put(21, pick(rows, r"Ⅳ\.영업외손익"))
    put(22, pick(rows, r"Ⅴ\.법인세비용차감전순이익"))
    put(23, pick(rows, r"Ⅵ\.법인세비용"))
    put(24, pick(rows, r"Ⅶ\.(분기|반기|당기)순이익"))
    r25 = pick(rows, r"(Ⅷ|Ⅸ)\.기타포괄손익")
    put(25, r25)
    r31 = [r for r in rows if r["lab"].endswith("총포괄손익")][-1]
    put(31, r31)
    # OCI leaves between 25 and 31
    i25, i31 = rows.index(r25), rows.index(r31)
    leaves = [r for r in rows[i25 + 1:i31] if re.match(r"^\(\d+\)", r["lab"])]
    claimed = {26: None, 27: None, 28: None, 30: None}
    rest = []
    for r in leaves:
        l = r["lab"]
        if "신용손실" in l:
            rest.append(r); continue
        if "재보험계약자산" in l:
            claimed[30] = r
        elif "보험계약자산" in l:
            claimed[27] = r
        elif "공정가치측정금융자산" in l and ("평가손익" in l or "관련손익" in l):
            claimed[26] = r
        elif "현금흐름위험회피" in l:
            claimed[28] = r
        else:
            rest.append(r)
    for k, r in claimed.items():
        put(k, r)
    it[29] = None; ct[29] = [("none printed", None)]
    it[32] = sum(f(val(r)) for r in rest)
    ct[32] = [(r["lab"], val(r)[1], val(r)[0]) for r in rest]
    return it, ct

SPEC = [  # (key, quarter, fy, ytd col, 3m col)
 ("later", "2023.1Q", "FY2024_Q1", 3, 2), ("later", "2023.2Q", "FY2024_Q2", 3, 2),
 ("later", "2023.3Q", "FY2024_Q3", 3, 2), ("later", "2023.4Q", "FY2024_Q4", 1, None),
 ("later", "2024.1Q", "FY2025_Q1", 3, 2), ("later", "2024.2Q", "FY2025_Q2", 3, 2),
 ("later", "2024.3Q", "FY2025_Q3", 3, 2), ("later", "2024.4Q", "FY2025_Q4", 1, None),
 ("later2", "2023.4Q", "FY2025_Q4", 2, None), ("later2", "2024.4Q", "FY2025_Q4", 1, None),
 ("orig", "2023.3Q", "FY2023_Q3", 1, 0), ("orig", "2023.4Q", "FY2023_Q4", 0, None),
 ("orig", "2024.1Q", "FY2024_Q1", 1, 0), ("orig", "2024.2Q", "FY2024_Q2", 1, 0),
 ("orig", "2024.3Q", "FY2024_Q3", 1, 0), ("orig", "2024.4Q", "FY2024_Q4", 0, None),
]
res, txt = {}, []
cache = {}
for kind, q, fy, cy, c3 in SPEC:
    if fy not in cache:
        cache[fy] = stmt_rows(fy)
    f, rows = cache[fy]
    it, ct = derive(rows, cy)
    entry = {"file": f, "fy": fy, "ytd_col": cy, "items": it, "cites": {str(k): v for k, v in ct.items()}}
    if c3 is not None:
        it3, ct3 = derive(rows, c3)
        entry["items3m"] = it3; entry["cites3m"] = {str(k): v for k, v in ct3.items()}
    res[f"{kind}|{q}"] = entry
    txt.append(f"== {kind} {q}  {f}  ytd col {cy} 3m col {c3}")
    for k in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32):
        ln = ct.get(k)
        txt.append(f"   item {k:2d}: ytd {it.get(k)}   cite {ln}" + (f"   3m {entry['items3m'].get(k)}" if c3 is not None else ""))
    # identities
    chk = []
    if None not in (it.get(1), it.get(17), it.get(20)): chk.append(f"20-(1+17)={it[20]-it[1]-it[17]:+.1f}")
    if None not in (it.get(22), it.get(24), it.get(23)): chk.append(f"22-24-23={it[22]-it[24]-it[23]:+.1f}")
    if None not in (it.get(24), it.get(25), it.get(31)): chk.append(f"31-24-25={it[31]-it[24]-it[25]:+.1f}")
    parts = sum((it.get(k) or 0) for k in (26, 27, 28, 29, 30, 32))
    if it.get(25) is not None: chk.append(f"25-parts={it[25]-parts:+.1f}")
    txt.append("   identities: " + ", ".join(chk))
io.open(EVD / "KR0005_s7_xml.json", "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1, default=str))
io.open(EVD / "KR0005_s7_xml.txt", "w", encoding="utf-8").write("\n".join(txt) + "\n")
