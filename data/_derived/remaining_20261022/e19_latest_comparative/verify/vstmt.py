"""Own statement reader: separate (4-2) comprehensive income statement -> item values (million won) for cur-cum and prior-cum columns."""
import re, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative/verify")
import vrd

ROM = re.compile(r"^(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ]+|[IVX]+)\s*[\.\)]?\s*")
NUMB = re.compile(r"^(?:\(\d+\)|\d+\)|\d+\.|[가-힣]\.)\s*")
UNIT = re.compile(r"단위\s*[:：]\s*([가-힣]+)")
SCALE = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "억원": 100.0}


def strip_label(s):
    s = ROM.sub("", s.strip())
    s = NUMB.sub("", s)
    s = re.sub(r"\s*\(주[\d,\s]*\)\s*$", "", s)
    return s.strip()


def read_separate_stmt(code, per):
    """returns dict(file, line, unit, rows=[(label, [vals])], ncol)"""
    res = []
    for p in vrd.find_xml(code, per):
        t = vrd.read_text(p)
        for tb in vrd.tables(t):
            if tb["title"].endswith("포괄손익계산서") and "연결" not in tb["title"] and len(tb["rows"]) > 15 and "자본변동" not in tb["rows"][0][0]:
                pre = t[max(0, tb["pos"] - 3000):tb["pos"]]
                us = UNIT.findall(pre)
                unit = us[-1] if us else None
                rows = []
                for r in tb["rows"]:
                    if len(r) < 2:
                        continue
                    lab = r[0]
                    vals = [vrd.num(c) for c in r[1:]]
                    rows.append((lab, vals))
                res.append({"file": p, "line": tb["line"], "unit": unit, "rows": rows, "title": tb["title"]})
    assert len(res) == 1, (code, per, len(res), [r["title"] for r in res])
    return res[0]


def columns(st):
    # find the ncol from the first data row with numbers
    n = 0
    for lab, vals in st["rows"]:
        k = len([v for v in vals if v is not None])
        if k:
            n = max(n, len(vals))
    return n


def item_values(st, which):
    """which: 'cur' or 'prior' cumulative. returns dict item -> value (million won) and notes"""
    unit = st["unit"]
    sc = SCALE.get(unit)
    if sc is None:
        raise ValueError("unit %r" % unit)
    ncol = None
    # take the modal length of rows having >=1 numeric values
    from collections import Counter
    c = Counter(len(v) for _, v in st["rows"] if any(x is not None for x in v))
    ncol = c.most_common(1)[0][0]
    if ncol == 4:
        idx = {"cur": 1, "prior": 3, "cur3": 0, "prior3": 2}[which]
    elif ncol in (2, 3):
        idx = {"cur": 0, "prior": 1}[which]
    else:
        raise ValueError("ncol %d" % ncol)
    rows = [(strip_label(l), (v[idx] if idx < len(v) else None)) for l, v in st["rows"] if len(v) == ncol]
    def first(pred, start=0, end=None):
        for i in range(start, len(rows) if end is None else end):
            if pred(rows[i][0]) and rows[i][1] is not None:
                return i
        return None
    out = {}
    i1 = first(lambda l: l == "보험손익")
    i17 = first(lambda l: l == "투자손익", (i1 or 0))
    i20 = first(lambda l: l.startswith("영업이익"), (i17 or 0))
    if i1 is not None:
        out[1] = rows[i1][1]
        j = first(lambda l: l == "기타사업비용", i1, i17)
        if j is not None:
            out[16] = rows[j][1]
        else:
            out[16] = None
    if i17 is not None:
        out[17] = rows[i17][1]
        # insurance finance within investment section
        def sumlab(lbls):
            tot = 0.0; got = False
            for k in range(i17 + 1, i20):
                if rows[k][0] in lbls and rows[k][1] is not None:
                    tot += rows[k][1]; got = True
            return tot if got else 0.0
        inc = sumlab({"보험금융수익", "재보험금융수익"})
        exp = sumlab({"보험금융비용", "재보험금융비용"})
        out[19] = inc - exp
        out[18] = out[17] - out[19]
    if i20 is not None:
        out[20] = rows[i20][1]
    j = first(lambda l: l == "영업외손익", i20 or 0)
    if j is not None: out[21] = rows[j][1]
    j22 = first(lambda l: l.startswith("법인세") and "차감전" in l, i20 or 0)
    if j22 is not None: out[22] = rows[j22][1]
    j23 = first(lambda l: l.startswith("법인세비용") or l.startswith("법인세(") or l == "법인세", (j22 or 0) + 1)
    if j23 is not None: out[23] = rows[j23][1]
    j24 = first(lambda l: ("순이익" in l or "순손익" in l) and "조정" not in l and "주당" not in l, (j23 or 0) + 1)
    if j24 is not None: out[24] = rows[j24][1]
    j25 = first(lambda l: l.startswith("기타포괄손익") and "공정가치" not in l, (j24 or 0) + 1)
    if j25 is not None: out[25] = rows[j25][1]
    j31 = first(lambda l: "총포괄손익" in l, (j25 or 0) + 1)
    if j31 is not None: out[31] = rows[j31][1]
    if j25 is not None and j31 is not None:
        sub = rows[j25 + 1:j31]
        def pick(pred):
            tot = 0.0; got = False
            for l, v in sub:
                if v is not None and pred(l):
                    tot += v; got = True
            return tot if got else None
        out[26] = pick(lambda l: "공정가치" in l and ("평가손익" in l or "관련손익" in l) and "지분" not in l and "유가증권" not in l and "기대신용" not in l and "재분류" not in l and "항목" not in l)
        out[27] = pick(lambda l: (not l.startswith("재보험")) and l.startswith("보험") and "금융" in l and ("순" in l))
        out[30] = pick(lambda l: l.startswith("재보험") and "금융" in l and "순" in l)
        out[28] = pick(lambda l: "위험회피" in l)
        out[29] = pick(lambda l: ("지분" in l or "유가증권" in l) and "평가손익" in l)
        s = sum(out[k] for k in (26, 27, 28, 29, 30) if out.get(k) is not None)
        out[32] = out[25] - s if out.get(25) is not None else None
    # scale
    for k in list(out):
        if out[k] is not None:
            out[k] = out[k] * sc
    return out, rows, ncol


def three_month(st, which):
    """3-month column (cur or prior) values for a few items (for set_dangi checks): returns dict label->value in million won"""
    sc = SCALE[st["unit"]]
    from collections import Counter
    c = Counter(len(v) for _, v in st["rows"] if any(x is not None for x in v))
    ncol = c.most_common(1)[0][0]
    assert ncol == 4
    idx = {"cur": 0, "prior": 2}[which]
    return [(strip_label(l), (v[idx] * sc if v[idx] is not None else None)) for l, v in st["rows"] if len(v) == ncol]
