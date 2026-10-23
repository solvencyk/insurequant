# -*- coding: utf-8 -*-
"""KR0072 notes readers used ONLY by kr0072_verify.py (independent of the planner): PL4 (CSM amortisation) from the 보험영업수익 구성내역 note, and the CSM roll-forward tables
(issued contracts, general model: columns 미래현금흐름 / 위험조정 / 보험계약마진 / 보험계약부채(자산)) of the SEPARATE notes ('5. 재무제표 주석')."""
import re

from kdb_raw import (all_tables, clean, header_paths, lines_of, mn, nspace, parse_num, section, table_rows, table_unit, unit_above)

NOTES_RE = r"^5\.\s*재무제표 주석"
ROLE_RE = re.compile(r"제\s*\d+\s*\((당|전)\)\s*기")


def numeric_cells(r):
    return [(c["text"], c["line"], parse_num(c["text"])) for c in r["cells"][1:] if parse_num(c["text"]) is not None and c["text"] != ""]


def first_text_above(L, a):
    """(1-based line, text) of the nearest non-empty visible text line above 0-based line a"""
    k = a - 1
    while k >= 0:
        t = clean(L[k])
        if t:
            return k + 1, t
        k -= 1
    return None, None


def pl4_note(rel, which="prior"):
    """'(3) 제공된 서비스의 보험계약마진' row of the 보험영업수익 및 재보험영업수익의 구성내역 table (rows '1. 보험영업수익' + '2. 재보험영업수익' + '합계'); the prior-period cumulative = the LAST numeric cell
    (quarterly reports print [당 3개월, 당 누적, 전 3개월, 전 누적] in the half-year / third-quarter reports and [당, 전] in Q1 / annual).  Returns the cell plus the 3개월 prior cell when 4 numerics."""
    L = lines_of(rel)
    lo, hi = section(L, NOTES_RE)
    want = nspace("(3) 제공된 서비스의 보험계약마진")
    hits = []
    for (ta, tb) in all_tables(L):
        if not (lo <= ta <= hi):
            continue
        rows = table_rows(L, ta, tb)
        labs = [nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if want in labs and nspace("1. 보험영업수익") in labs and nspace("2. 재보험영업수익") in labs and ("합계" in labs or "보험서비스수익합계" in labs):
            hits.append((ta, tb, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{rel}: {len(hits)} 구성내역 tables (need 1): {[(h[0] + 1, h[1] + 1) for h in hits]}")
    ta, tb, rows = hits[0]
    un, unl, uwhere = table_unit(L, ta, tb)
    hdr = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "구분")
    heads = [c["text"] for c in hdr["cells"][1:]]
    row = [r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == want]
    if len(row) != 1:
        raise RuntimeError(f"{rel}: {len(row)} rows (3) 제공된 서비스의 보험계약마진")
    row = row[0]
    nums = numeric_cells(row)
    if which == "prior":
        t, ln, v = nums[-1]
    elif which == "cur":      # cumulative of the CURRENT period: 2nd of 4 numerics (3개월 / 누적 pairs) or the 1st of 2
        t, ln, v = nums[1] if len(nums) == 4 else nums[0]
    else:
        raise ValueError(which)
    out = dict(printed=t, line=ln, unit=un, unit_line=unl, unit_where=uwhere, mn=mn(t, un), table=(ta + 1, tb + 1), n_numeric=len(nums), heads=heads, label=row["cells"][0]["text"], label_line=row["cells"][0]["line"])
    if len(nums) == 4:
        t3, ln3, _ = nums[2]
        out["prior_3m"] = dict(printed=t3, line=ln3, mn=mn(t3, un))
        out["cur_3m"] = dict(printed=nums[0][0], line=nums[0][1], mn=mn(nums[0][0], un))
        out["cur_cum"] = dict(printed=nums[1][0], line=nums[1][1], mn=mn(nums[1][0], un))
    return out


CSM_CORE = {
    1: lambda c: c == "1.기초보험계약자산및부채",
    2: lambda c: c == "(3)최초인식한계약의효과",
    3: lambda c: c == "6.보험금융손익",
    4: lambda c: c == "(1)보험계약마진을조정하는추정치의변동분",
    5: lambda c: c == "(1)서비스이전을반영하기위해당기손익으로인식한보험계약마진",
    6: lambda c: re.match(r"^9\.(당분기말|당반기말|당기말|전분기말|전반기말|전기말|분기말|반기말|기말)보험계약자산및부채", c) is not None,
}
CSM_EXTRA = {"asset_open": lambda c: c == "(1)기초보험계약자산", "fin_pl": lambda c: c == "(1)당기손익", "fin_oci": lambda c: c == "(2)기타포괄손익",
             "future": lambda c: c == "2.미래서비스관련변동", "current": lambda c: c == "3.현행서비스관련변동", "past": lambda c: c == "4.과거서비스관련변동",
             "isr": lambda c: c.startswith("5.보험서비스결과")}


def csm_tables(rel, lo=None, hi=None):
    """CSM roll-forward tables of the ISSUED contracts in the separate notes: {role: dict(rows{item: cell}, extra{...}, table, caption, unit, col)}; role from the nearest visible text line above the table
    ('제 N(당)기 ...' = cur, '제 N(전)기 ...' = prior).  Exactly one table per role is required."""
    L = lines_of(rel)
    if lo is None:
        lo, hi = section(L, NOTES_RE)
    out = {}
    for (ta, tb) in all_tables(L):
        if not (lo <= ta <= hi):
            continue
        rows = table_rows(L, ta, tb)
        hdr = next((r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "구분"), None)
        if hdr is None:
            continue
        heads = [nspace(c["text"]) for c in hdr["cells"]]
        if heads[1:] != [nspace(x) for x in ("미래현금흐름의현재가치 추정치", "비금융위험에대한 위험조정", "보험계약마진", "보험계약부채(자산)")]:
            continue
        cores = [nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if "1.기초보험계약자산및부채" not in cores:
            continue
        jcsm = heads.index("보험계약마진")
        cap_line, cap_txt = first_text_above(L, ta)
        m = ROLE_RE.search(cap_txt or "")
        role = None if m is None else ("cur" if m.group(1) == "당" else "prior")
        un, unl, uwhere = table_unit(L, ta, tb)
        res, extra = {}, {}
        for item, f in CSM_CORE.items():
            hit = [r for r in rows if r["cells"] and f(nspace(r["cells"][0]["text"]))]
            if len(hit) != 1:
                res[item] = None
                continue
            r = hit[0]
            if len(r["cells"]) != len(heads):
                raise RuntimeError(f"{rel}: CSM row {r['cells'][0]['text']!r} has {len(r['cells'])} cells, header {len(heads)}")
            c = r["cells"][jcsm]
            res[item] = dict(label=r["cells"][0]["text"], label_line=r["cells"][0]["line"], printed=c["text"], line=c["line"], mn=mn(c["text"], un))
        for name, f in CSM_EXTRA.items():
            hit = [r for r in rows if r["cells"] and f(nspace(r["cells"][0]["text"]))]
            if len(hit) == 1:
                c = hit[0]["cells"][jcsm]
                extra[name] = dict(label=hit[0]["cells"][0]["text"], printed=c["text"], line=c["line"], mn=mn(c["text"], un))
        if role in out:
            raise RuntimeError(f"{rel}: two issued CSM tables with role {role}: {out[role]['table']} and {(ta + 1, tb + 1)}")
        out[role] = dict(rows=res, extra=extra, table=(ta + 1, tb + 1), caption=(cap_line, cap_txt), unit=un, unit_line=unl, unit_where=uwhere, col=jcsm, heads=heads)
    return out
