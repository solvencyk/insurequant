"""Statement-row helpers (own code) for PL tier-1 definitions."""
import re
from lib_dart import *

def strip_prefix(lab):
    l = lab.replace(" ", "")
    l = re.sub(r"^(\(?[0-9]+\)|[0-9]+\.|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫⅬⅭ]+\.?|[IVX]+\.|[가-힣]\.)+", "", l)
    l = re.sub(r"\((손실|수익|이익)\)$", "", l)
    return l

def stmt_rows(tab):
    """list of (clean_label, [numeric values in order]) for a statement-like table"""
    out = []
    for r in tab["rows"]:
        lab = None; vals = []
        for c in r:
            if is_num(c) or c.strip() in ("-", "–", "—", "−"):
                if lab is not None: vals.append(0.0 if c.strip() in ("-", "–", "—", "−") else to_num(c))
            else:
                if lab is None and c.strip(): lab = c
        if lab is not None: out.append((strip_prefix(lab), vals, lab))
    return out

def is_statement(tab):
    labs = [x[0] for x in stmt_rows(tab)]
    s = " ".join(labs)
    return ("영업이익" in s) and re.search(r"(분기|반기|당기)?순이익|순손익", s) and ("법인세" in s)

def first(rows, *pats, exact=True):
    for lab, vals, raw in rows:
        for p in pats:
            if (exact and lab == p) or (not exact and re.search(p, lab)):
                return vals
    return None

def define(rows, item):
    """item definitions on a statement (returns vector aligned to the printed columns, or None)"""
    def vec(*pats, exact=True): return first(rows, *pats, exact=exact)
    def comb(pos, neg):
        vs = [vec(p) for p in pos] + [vec(p) for p in neg]
        if any(v is None for v in vs[:len(pos)]) and not pos: return None
        n = max(len(v) for v in vs if v is not None) if any(v is not None for v in vs) else 0
        res = [0.0] * n
        for p in pos:
            v = vec(p)
            if v:
                for i in range(n): res[i] += v[i] if i < len(v) else 0
        for p in neg:
            v = vec(p)
            if v:
                for i in range(n): res[i] -= v[i] if i < len(v) else 0
        return res
    if item == 1: return vec("보험손익", "보험서비스결과", "보험영업손익")
    if item == 17:
        v = vec("투자손익", "투자영업손익")
        if v: return v
        a, b = vec("투자영업수익"), vec("투자영업비용")
        return [x - y for x, y in zip(a, b)] if a and b else None
    if item == 19:
        # cost rows are printed positive in some filings and negative (parentheses) in others: add the row when it is printed negative
        res = None
        for pat, sign in (("보험금융수익", 1), ("재보험금융수익", 1), ("보험금융비용", -1), ("재보험금융비용", -1)):
            v = vec(pat)
            if v is None: continue
            if sign == -1 and v and all(x <= 0 for x in v if x != 0) and any(x < 0 for x in v): sign = 1
            if res is None: res = [0.0] * len(v)
            for i in range(len(res)):
                res[i] += sign * (v[i] if i < len(v) else 0.0)
        return res
    if item == 18:
        v17, v19 = define(rows, 17), define(rows, 19)
        return [a - b for a, b in zip(v17, v19)] if v17 and v19 else None
    if item == 20: return vec("영업이익")
    if item == 21:
        v = vec("영업외손익")
        if v: return v
        a, b = vec("영업외수익"), vec("영업외비용")
        return [x - y for x, y in zip(a, b)] if a and b else None
    if item == 22: return vec(r"법인세비용차감전.*이익", r"법인세차감전.*이익", r"세전.*이익", exact=False)
    if item == 23: return vec("법인세비용", "법인세")
    if item == 24: return vec(r"^(분기|반기|당기)?순이익|^(분기|반기|당기)순", exact=False)
    return None


def define_all(rows, item):
    """extended definitions incl. OCI items (25-32), 15, 16, 23 (abs)"""
    if item in (1, 17, 18, 19, 20, 21, 22, 24): return define(rows, item)
    def vec(*pats, exact=True): return first(rows, *pats, exact=exact)
    if item == 15:
        v = vec("기타영업수익")
        return v if v else None
    if item == 16:
        v = vec("기타사업비용")
        return [abs(x) for x in v] if v else None
    if item == 23:
        v = vec("법인세비용", "법인세")
        return [abs(x) for x in v] if v else None
    if item == 25: return vec("기타포괄손익")
    if item == 31: return vec("총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익", r"총포괄손익$", exact=False)
    if item == 26: return vec(r"기타포괄손익-공정가치측정(금융자산|채무)", r"기타포괄손익-공정가치측정금융자산관련손익", r"기타포괄손익-공정가치측정채무", exact=False)
    if item == 27: return vec(r"^보험계약자산\(부채\)순금융손익", r"보험계약.*순금융손익", exact=False)
    if item == 28: return vec(r"현금흐름위험회피.*평가손익", exact=False)
    if item == 29: return vec(r"기타포괄손익-공정가치측정유가증권평가손익", r"기타포괄손익-공정가치측정지분", exact=False)
    if item == 30: return vec(r"^재보험계약자산\(부채\)순금융손익", exact=False)
    if item == 32:
        v25 = vec("기타포괄손익")
        parts = [define_all(rows, i) for i in (26, 27, 28, 29, 30)]
        if v25 is None: return None
        return [v25[k] - sum((p[k] if p and k < len(p) else 0.0) for p in parts) for k in range(len(v25))]
    return None
