# -*- coding: utf-8 -*-
"""KR0099 KB라이프 (ticket 20261023T0900Z, D1 option B) -- INDEPENDENT re-read of EVERY planned cell.
Own code: imports only the standard library (no e21_* / e23_* / mlib / scripts / src module), so it cannot share a defect with the planner.

For each cell cited by e23_plan_kblife.json (physical xml line, printed text, sign, abs, unit) the script
  * opens that physical line, rebuilds the whole <TR> from the raw lines (blank cells included) and parses the printed number itself (parentheses = negative, '-' = 0),
  * derives the LOGICAL COLUMN of the cell from the colspans of the cells before it and maps it to the table header (THEAD grid with COLSPAN / ROWSPAN),
    then requires: statement -> prior-year group of the second period title line, sub-column '누적' (prior-year cumulative); 보험영업수익 note -> prior-period group, last column 합계 (cumulative
    block); CSM roll-forward -> prior-period group, column 보험계약마진,
  * checks the row label, the unit line above, the section TITLE above (4-2 separate statement / 5. separate notes; never the consolidated 2-2 / 3.),
  * recomputes the value from the printed cells and compares it with the plan,
  * re-checks statement-internal identities from freshly read printed cells (pins the duplicated '보험영업수익' / '보험영업비용' occurrences),
  * re-reads the printed prior 3-month column and compares it with the single quarter that the load would derive (cum(q) - cum(q-1)),
  * compares the plan `old` values with git HEAD, and the apply contract with HEAD gold,
  * re-computes the PL identities and the CSM closure on the merged vectors.
Writes kr0099_verify.txt / kr0099_verify.json next to this file; exit code 1 when anything fails."""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
import os
PLAN = json.loads((HERE / os.environ.get("KR0099_PLAN", "e23_plan_kblife.json")).read_text(encoding="utf-8"))
OUTTAG = os.environ.get("KR0099_OUTTAG", "")
CODE = PLAN["code"]
TAG = re.compile(r"<[^>]+>")
_cache = {}
PROBLEMS = []
NOTES = []


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("\u3000", " ").replace("\xa0", " ")).strip()


def parse_num(t):
    t = (t or "").strip().replace(",", "").replace(" ", "")
    if t == "":
        return None
    if t in ("-", "\u2212"):
        return 0.0
    neg = t.startswith("(") and t.endswith(")")
    t2 = t.strip("()")
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


def git_json(rel):
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout
    return json.loads(out.decode("utf-8"))


def nspace(s):
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


def problem(where, msg):
    PROBLEMS.append(dict(where=where, problem=msg))


# ------------------------------------------------------------------------------------------------ raw table machinery (independent implementation)
def tr_bounds(L, ln):
    i = ln - 1
    while i > 0 and not re.match(r"\s*<TR", L[i], re.I):
        i -= 1
    j = ln - 1
    while j < len(L) - 1 and not re.match(r"\s*</TR", L[j], re.I):
        j += 1
    return i, j


def parse_tr(L, i, j):
    """cells of the TR spanning lines i..j (0-based inclusive): [dict(tag, colspan, rowspan, text, line)]  (blank cells included; line = physical line of the first text, else of the tag)"""
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            attrs = m.group(2)
            cs = re.search(r'COLSPAN="(\d+)"', attrs, re.I)
            rs = re.search(r'ROWSPAN="(\d+)"', attrs, re.I)
            rest = m.group(3)
            colspan = int(cs.group(1)) if cs else 1
            rowspan = int(rs.group(1)) if rs else 1
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out.append(dict(tag=m.group(1).upper(), colspan=colspan, rowspan=rowspan, text=clean(rest), line=k + 1))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", L[q], re.I):
                    t = clean(L[q])
                    if t:
                        buf.append(t)
                        if tl is None:
                            tl = q + 1
                    q += 1
                out.append(dict(tag=m.group(1).upper(), colspan=colspan, rowspan=rowspan, text=" ".join(buf).strip(), line=tl or (k + 1)))
                k = q
        k += 1
    return out


def table_bounds(L, ln):
    a = ln - 1
    while a > 0 and not re.match(r"\s*<TABLE\b", L[a], re.I):
        a -= 1
    b = ln - 1
    while b < len(L) - 1 and not re.match(r"\s*</TABLE", L[b], re.I):
        b += 1
    return a, b


def header_paths(L, a, b):
    """logical column index -> header path (texts top to bottom, rowspan repeats removed) from the THEAD of the table spanning lines a..b"""
    h0 = next((k for k in range(a, b + 1) if re.match(r"\s*<THEAD", L[k], re.I)), None)
    h1 = next((k for k in range(h0 or a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), None)
    if h0 is None or h1 is None:
        return None
    trs, k = [], h0
    while k <= h1:
        if re.match(r"\s*<TR", L[k], re.I):
            i0 = k
            while not re.match(r"\s*</TR", L[k], re.I):
                k += 1
            trs.append((i0, k))
        k += 1
    grid, occ, ncols = {}, set(), 0
    for r, (i0, j0) in enumerate(trs):
        col = 0
        for c in parse_tr(L, i0, j0):
            while (r, col) in occ:
                col += 1
            for dr in range(c["rowspan"]):
                for dc in range(c["colspan"]):
                    occ.add((r + dr, col + dc))
                    grid[(r + dr, col + dc)] = c["text"]
            col += c["colspan"]
        ncols = max(ncols, col)
    paths = []
    for col in range(ncols):
        path = []
        for r in range(len(trs)):
            t = grid.get((r, col))
            if t is not None and (not path or path[-1] != t):
                path.append(t)
        paths.append(path)
    return paths


def logical_col(cells, ln):
    """(logical column index, cell) of the cell whose text line == ln"""
    col = 0
    for c in cells:
        if c["line"] == ln:
            return col, c
        col += c["colspan"]
    return None, None


def unit_above(L, ln, span=6000):
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


def title_above(L, ln):
    for k in range(ln - 1, 0, -1):
        if L[k].startswith("<TITLE"):
            t = clean(L[k])
            if t:
                return t, k + 1
    return "", 0


def top_title_above(L, ln):
    """nearest preceding top-level section title ('N. ...' or 'N-M. ...' with ATOC=Y)"""
    for k in range(ln - 1, 0, -1):
        if L[k].startswith("<TITLE") and 'ATOC="Y"' in L[k]:
            t = clean(L[k])
            if re.match(r"^\d+(-\d+)?\.", t):
                return t, k + 1
    return "", 0


def norm_label(s):
    s = nspace(s)
    s = re.sub(r"^([\u2160-\u2169]|[IVX]+|\d+)\.", "", s)
    s = re.sub(r"^\(\d+\)", "", s)
    s = re.sub(r"\(주[^)]*\)", "", s)
    return s.replace("(손실)", "").replace("(수익)", "").replace("(이익)", "")


SCALE = {"원": 1e6, "천원": 1e3, "백만원": 1.0}
CSM_SCALE = {"원": 1e8, "천원": 1e5, "백만원": 100.0}
PRIOR_WORDS = ("전분기", "전반기", "전기")


def qend(q):
    return {"1": "03.31", "2": "06.30", "3": "09.30", "4": "12.31"}[q[5]]


# ------------------------------------------------------------------------------------------------ statement (4-2) reader
class Stmt:
    """independent reader of the separate comprehensive income statement of one filing: rows with ALL value cells, logical columns, header paths, period title lines"""

    def __init__(self, rel, quarter):
        self.rel, self.L, self.q = rel, lines_of(rel), quarter
        L = self.L
        self.tl = next((k + 1 for k, s in enumerate(L) if s.startswith("<TITLE") and re.search(r"4-2\.\s*포괄손익계산서", s)), None)
        if self.tl is None:
            raise RuntimeError(f"{rel}: no 4-2 title")
        nxt = next((k + 1 for k in range(self.tl, len(L)) if L[k].startswith("<TITLE")), len(L))
        self.end = nxt
        # period title lines (inside the pre-header table, between the title and the first <THEAD)
        thead = next(k + 1 for k in range(self.tl, nxt) if re.match(r"\s*<THEAD", L[k], re.I))
        per = []
        for k in range(self.tl, thead):
            m = re.search(r"(제\s*\d+\s*기\s*\S+)\s+(\d{4})\.(\d{2}\.\d{2})\s*부터\s*(\d{4})\.(\d{2}\.\d{2})\s*까지", clean(L[k]))
            if m:
                per.append(dict(label=nspace(m.group(1)), y0=m.group(2), d0=m.group(3), y1=m.group(4), d1=m.group(5), line=k + 1))
        self.periods = per
        self.unit, self.unit_line = unit_above(L, thead)
        a, b = table_bounds(L, thead + 3)
        self.tab = (a, b)
        self.paths = header_paths(L, a, b)
        self.rows = []
        k = a
        while k <= b:
            if re.match(r"\s*<TR", L[k], re.I):
                i0 = k
                while not re.match(r"\s*</TR", L[k], re.I):
                    k += 1
                cells = parse_tr(L, i0, k)
                body = [c for c in cells if c["tag"] in ("TE", "TD")]
                if body:
                    self.rows.append(dict(tr=i0 + 1, cells=body, label=body[0]["text"], vals=body[1:]))
            k += 1

    def prior_col(self, kind):
        """logical column of the prior-year (second period) group: kind 'cum' -> sub-column 누적, '3m' -> 3개월"""
        if len(self.periods) != 2:
            raise RuntimeError(f"{self.rel}: {len(self.periods)} period lines")
        want = self.periods[1]["label"]
        sub = "누적" if kind == "cum" else "3개월"
        hits = [i for i, p in enumerate(self.paths) if len(p) >= 2 and nspace(p[0]) == want and nspace(p[1]) == sub]
        if len(hits) != 1:
            raise RuntimeError(f"{self.rel}: header columns for ({want}, {sub}) = {hits}; paths {self.paths}")
        return hits[0]

    def rows_by_label(self, label):
        return [r for r in self.rows if norm_label(r["label"]) == norm_label(label)]

    def cell(self, row, logical):
        col = 0
        for c in row["cells"]:
            if col == logical:
                return c
            col += c["colspan"]
        return None

    def get(self, label, nth, kind="cum", prior=True):
        rs = self.rows_by_label(label)
        if len(rs) < nth:
            raise RuntimeError(f"{self.rel}: label {label!r} occurs {len(rs)} times (< {nth})")
        r = rs[nth - 1]
        c = self.cell(r, self.prior_col(kind))
        if c is None:
            return None, None
        return parse_num(c["text"]), c


# ------------------------------------------------------------------------------------------------ per-cell citation check
def check_statement_part(st, p, where):
    """cited statement cell must be the prior-year cumulative cell of its row"""
    L = st.L
    ln = p["line"]
    i, j = tr_bounds(L, ln)
    cells = parse_tr(L, i, j)
    col, c = logical_col(cells, ln)
    if c is None:
        problem(where, f"L{ln}: no cell text on the cited line")
        return None
    v = parse_num(c["text"])
    pr = parse_num(p["printed"])
    if v is None or pr is None or abs(v - pr) > 1e-9 or nspace(c["text"]) != nspace(p["printed"]):
        problem(where, f"L{ln}: printed {p['printed']!r} != raw {c['text']!r}")
    if not (st.tab[0] <= i <= st.tab[1]):
        problem(where, f"L{ln}: not inside the 4-2 statement table")
    expect = st.prior_col("cum")
    if col != expect:
        problem(where, f"L{ln}: logical column {col} != prior-year cumulative column {expect} (path {st.paths[col] if col is not None and col < len(st.paths) else None})")
    lab = cells[0]["text"] if cells else ""
    if norm_label(lab) != norm_label(p["label"]):
        problem(where, f"L{ln}: row label {lab!r} != plan label {p['label']!r}")
    if p["unit"] != st.unit:
        problem(where, f"L{ln}: unit {st.unit} (L{st.unit_line}) != plan {p['unit']}")
    return v


def contrib(p):
    v = parse_num(p["printed"])
    return p["sign"] * (abs(v) if p.get("abs") else v) / SCALE[p["unit"]]


# ------------------------------------------------------------------------------------------------ notes (5. separate notes)
def note_table_of(L, ln):
    a, b = table_bounds(L, ln)
    return a, b, header_paths(L, a, b)


def check_pl4_part(p, where, quarter):
    """item 4: row '서비스제공에 따른 보험계약마진의 변동' of the prior-period 보험영업수익 note, last column = 합계 of the (cumulative) block"""
    rel = PLAN_REL[(quarter, "xml")]
    L = lines_of(rel)
    ln = p["line"]
    i, j = tr_bounds(L, ln)
    cells = parse_tr(L, i, j)
    col, c = logical_col(cells, ln)
    if c is None:
        problem(where, f"PL4 L{ln}: no cell text")
        return None
    a, b, paths = note_table_of(L, ln)
    top, tln = top_title_above(L, ln)
    if not re.match(r"^5\.\s*재무제표\s*주석", top):
        problem(where, f"PL4 L{ln}: section {top!r} (L{tln}) is not '5. 재무제표 주석' (separate notes)")
    lab = norm_label(cells[0]["text"])
    if lab != norm_label("서비스제공에 따른 보험계약마진의 변동"):
        problem(where, f"PL4 L{ln}: row label {cells[0]['text']!r}")
    path = paths[col] if paths and col < len(paths) else None
    ok = path and nspace(path[0]) in PRIOR_WORDS and nspace(path[-1]) == "합계" and (len(path) == 2 or nspace(path[1]) == "누적")
    if not ok:
        problem(where, f"PL4 L{ln}: header path {path} is not [prior period, (누적), 합계]")
    if col != len(paths) - 1:
        problem(where, f"PL4 L{ln}: logical column {col} is not the last column {len(paths) - 1}")
    # the table must be the prior-period twin of the 보험영업수익 note and the first 보험수익 section row (not the reinsurance 제공받은 서비스의 재보험계약마진 row)
    if nspace(paths[1][0]) not in PRIOR_WORDS:
        problem(where, f"PL4 L{ln}: table header group {paths[1][0]!r} is not a prior period")
    u, uln = unit_above(L, ln)
    if u != p["unit"]:
        problem(where, f"PL4 L{ln}: unit {u} != plan {p['unit']}")
    v = parse_num(c["text"])
    if nspace(c["text"]) != nspace(p["printed"]):
        problem(where, f"PL4 L{ln}: printed {p['printed']!r} != raw {c['text']!r}")
    # sibling check: the first 'bold' row of the 보험수익 section must carry the same row once (the row appears once per table)
    rows_lab = []
    k = a
    while k <= b:
        if re.match(r"\s*<TR", L[k], re.I):
            i0 = k
            while not re.match(r"\s*</TR", L[k], re.I):
                k += 1
            cs = parse_tr(L, i0, k)
            if cs:
                rows_lab.append(norm_label(cs[0]["text"]))
        k += 1
    if rows_lab.count(norm_label("서비스제공에 따른 보험계약마진의 변동")) != 1:
        problem(where, f"PL4 L{ln}: row label occurs {rows_lab.count(norm_label('서비스제공에 따른 보험계약마진의 변동'))} times in the table")
    return v


CSM_LABELS = {
    1: lambda x: x == "기초순장부금액",
    2: lambda x: x == "신계약효과",
    3: lambda x: x == "보험금융손익(PL)",
    4: lambda x: x == "보험계약마진을조정하는추정치변동",
    5: lambda x: x == "서비스제공에따른보험계약마진변동",
    6: lambda x: re.match(r"^(분기말|반기말|기말)순장부금액$", x) is not None,
}


def check_csm_part(p, item, rel, where):
    L = lines_of(rel)
    ln = p["line"]
    i, j = tr_bounds(L, ln)
    cells = parse_tr(L, i, j)
    col, c = logical_col(cells, ln)
    if c is None:
        problem(where, f"CSM L{ln}: no cell text")
        return None
    a, b, paths = note_table_of(L, ln)
    top, tln = top_title_above(L, ln)
    if not re.match(r"^5\.\s*재무제표\s*주석", top):
        problem(where, f"CSM L{ln}: section {top!r} is not '5. 재무제표 주석'")
    lab = nspace(cells[0]["text"])
    if not CSM_LABELS[item](lab):
        problem(where, f"CSM L{ln}: row label {cells[0]['text']!r} is not the expected row of item {item}")
    path = paths[col] if paths and col < len(paths) else None
    if not (path and nspace(path[0]) in PRIOR_WORDS and nspace(path[-1]) == "보험계약마진"):
        problem(where, f"CSM L{ln}: header path {path} is not [prior period, 보험계약마진]")
    # the table must be the ISSUED-contract roll-forward: the nearest caption paragraph above (<=2 tables up) names the 보험계약부채(자산), never the 재보험계약자산(부채)
    cap = None
    tabs_seen = 0
    for k in range(a - 1, max(a - 4000, 0), -1):
        if re.match(r"\s*<TABLE\b", L[k], re.I):
            tabs_seen += 1
            if tabs_seen > 1:
                break
        m = re.search(r"측정요소\s*별\s*변동내역", L[k])
        if m:
            cap = clean(L[k])
            break
    if cap is None or "보험계약부채(자산)" not in cap or "재보험계약자산" in cap or "적용하지 않은" not in cap:
        problem(where, f"CSM L{ln}: caption above {cap!r} is not the issued-contract (PAA 미적용) roll-forward")
    u, uln = unit_above(L, ln)
    if u != p["unit"]:
        problem(where, f"CSM L{ln}: unit {u} != plan {p['unit']}")
    if nspace(c["text"]) != nspace(p["printed"]):
        problem(where, f"CSM L{ln}: printed {p['printed']!r} != raw {c['text']!r}")
    return parse_num(c["text"])


PLAN_REL = {}


def main():
    txt = []
    pl_head = git_json("PL_breakdown.json")
    HM = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in pl_head}
    HD = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in pl_head}
    csm_head = git_json("CSM_waterfall.json")
    CM = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in csm_head}
    CD = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in csm_head}
    gold = git_json("data/_gold/user_pl_cells.json")
    goldc = git_json("data/_gold/user_csm_cells.json")
    G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in goldc["set"]}
    nd = {tuple(x) for x in gold["null_dangi"]["cells"]}
    sd = {(x[0], x[1], int(x[2])) for x in gold["set_dangi"]["cells"]}
    CON = PLAN["apply_contract"]
    plan_val = {(c["code"], c["item"], c["quarter"]): c["new"] for b in PLAN["buckets"] for c in b["cells"]}

    n_cells = n_ok = 0
    stm = {}
    for b in PLAN["buckets"]:
        q = b["quarter"]
        rel = b["meta"]["file"]
        PLAN_REL[(q, "xml")] = rel
        st = Stmt(rel, q)
        stm[q] = st
        # period lines: the second period must be the prior-year cumulative period of the quarter
        y = q[:4]
        per = st.periods
        if len(per) != 2 or not (per[1]["y0"] == y and per[1]["d0"] == "01.01" and per[1]["y1"] == y and per[1]["d1"] == qend(q)):
            problem(f"{q} statement", f"period lines {per} are not [current, {y}.01.01-{y}.{qend(q)}]")
        top, tln = top_title_above(st.L, st.tab[0] + 1)
        if not re.match(r"^4-2\.\s*포괄손익계산서", top):
            problem(f"{q} statement", f"section title {top!r} is not '4-2. 포괄손익계산서' (separate)")
        if st.unit != "백만원":
            problem(f"{q} statement", f"unit {st.unit}")
        txt.append(f"{q}: {rel} unit {st.unit} (L{st.unit_line}); periods {[(p['label'], p['y0'] + '.' + p['d0'] + '-' + p['y1'] + '.' + p['d1']) for p in per]}; prior-cum column {st.prior_col('cum')} path {st.paths[st.prior_col('cum')]}")
    # ---- statement-internal identities from FRESH reads of the prior cumulative column (pin the duplicated-label occurrences)
    for q, st in stm.items():
        g = lambda lab, n=1: st.get(lab, n)[0]   # noqa: E731
        fin_sec = st.rows_by_label("보험금융손익")
        idn = []
        r7, r8, r9 = g("보험영업수익", 1), g("보험영업수익", 2), g("재보험영업수익", 1)
        r10, r11, r12, r13 = g("보험영업비용", 1), g("보험영업비용", 2), g("재보험영업비용", 1), g("기타사업비용", 1)
        idn.append(("보험영업수익(총) = 보험영업수익 + 재보험영업수익", r7, r8 + r9))
        idn.append(("보험영업비용(총) = 보험영업비용 + 재보험영업비용 + 기타사업비용", r10, r11 + r12 + r13))
        ins = g("보험영업손익")
        idn.append(("보험영업손익 = 총수익 - 총비용", ins, r7 - r10))
        inv = g("투자영업손익")
        fin = (g("보험금융손익") if fin_sec else 0.0)
        oper = g("영업이익")
        idn.append(("영업이익 = 보험영업손익 + 투자영업손익 + 보험금융손익(별도 구간일 때)", oper, ins + inv + fin))
        nonop = g("영업외손익")
        pre = g("법인세비용차감전순이익")
        idn.append(("세전이익 = 영업이익 + 영업외손익", pre, oper + nonop))
        tax = g("법인세비용")
        ni = g("당기순이익(손실)")
        idn.append(("당기순이익 = 세전이익 - 법인세", ni, pre - tax))
        oci = g("기타포괄손익")
        tot = g("총포괄손익")
        idn.append(("총포괄손익 = 당기순이익 + 기타포괄손익", tot, ni + oci))
        leaves = [g(lab) for lab in ("순확정급여부채의 재측정요소", "기타포괄손익-공정가치측정지분상품평가손익", "기타포괄손익-공정가치측정채무상품평가손익", "보험계약자산부채순금융손익", "재보험계약자산부채순금융손익", "현금흐름위험회피파생상품평가손익")]
        idn.append(("기타포괄손익 = 6개 리프 합", oci, sum(leaves)))
        if not fin_sec:
            ifin = (g("보험금융수익") + g("재보험금융수익")) - (g("보험금융비용") + g("재보험금융비용"))
            idn.append(("투자영업손익 안에 보험금융(수익-비용)이 포함돼 있음 -> 보험금융손익 = 투자영업수익 - 투자영업비용 내 구성", None, None))
        for name, l, r in idn:
            if l is None:
                continue
            ok = abs(l - r) <= 0.5
            txt.append(f"  {q} identity {name}: {l:g} vs {r:g} {'ok' if ok else 'FAIL'}")
            if not ok:
                problem(f"{q} identity", f"{name}: {l} vs {r}")

    # ---- every PL cell
    pos_stat = defaultdict(Counter)
    for b in PLAN["buckets"]:
        code, q = b["code"], b["quarter"]
        st = stm[q]
        for c in b["cells"]:
            n_cells += 1
            key = (code, c["item"], q)
            where = f"{code} {q} i{c['item']}"
            n_before = len(PROBLEMS)
            ho = HM.get(key)
            if (ho is None) != (c["old"] is None) or (ho is not None and abs(ho - c["old"]) > 5e-7):
                problem(where, f"old {c['old']} != HEAD master {ho}")
            if key in G:
                problem(where, "owner gold exists at HEAD for a cell planned as new")
            tot = 0.0
            for p in c["parts"]:
                if c["item"] == 4:
                    v = check_pl4_part(p, where, q)
                else:
                    v = check_statement_part(st, p, where)
                tot += contrib(p)
                if v is not None:
                    pos_stat[q]["checked"] += 1
            if c.get("abs_of_sum"):
                tot = abs(tot)
            for o in c["operands"]:
                if o["source"] == "master HEAD":
                    mv = HM.get((code, o["item"], q))
                    if mv is None or abs(mv - o["value"]) > 5e-7:
                        problem(where, f"operand {o['item']} {o['value']} != HEAD master {mv}")
                else:
                    pv = plan_val.get((code, o["item"], q))
                    if pv is None or abs(pv - o["value"]) > 1e-6:
                        problem(where, f"operand {o['item']} {o['value']} != plan cell {pv}")
                tot += o["sign"] * o["value"]
            if abs(tot - c["new"]) > 1e-6:
                problem(where, f"recomputed {tot} != plan {c['new']}")
            if len(PROBLEMS) == n_before:
                n_ok += 1
    txt.append(f"PL cells: {n_cells}, all checks ok {n_ok}")

    # ---- operand basis: items 5 / 6 of the HEAD master (used in the residual item 7) equal the prior-period note of the later filing; items 9 / 10 / 11 reported
    for b in PLAN["buckets"]:
        q = b["quarter"]
        rel = b["meta"]["file"]
        L = lines_of(rel)
        ln4 = next(c for c in b["cells"] if c["item"] == 4)["parts"][0]["line"]
        a, bb, paths = note_table_of(L, ln4)
        rows = {}
        k = a
        while k <= bb:
            if re.match(r"\s*<TR", L[k], re.I):
                i0 = k
                while not re.match(r"\s*</TR", L[k], re.I):
                    k += 1
                cs = parse_tr(L, i0, k)
                if cs:
                    rows.setdefault(norm_label(cs[0]["text"]), []).append(cs)
            k += 1
        def last(lab):
            return parse_num(rows[norm_label(lab)][0][-1]["text"])
        i5 = abs(last("위험해제에 따른 위험조정의 변동 (보험수익)"))
        i6 = abs(last("예상보험금 및 예상보험서비스 비용")) - abs(last("실제보험금 및 실제보험서비스비용"))
        i9 = -abs(last("제공받은 서비스의 재보험계약마진"))
        i10 = -abs(last("위험해제로 인한 위험조정의 변동"))
        i11 = abs(last("발생 재보험금 및 재보험서비스비용 회수액")) - abs(last("회수예상 보험금 및 보험서비스비용"))
        m = {i: HM.get((CODE, i, q)) for i in (5, 6, 9, 10, 11)}
        txt.append(f"  {q} note legs (prior period, 합계 cumulative): i5 {i5:g} vs master {m[5]}; i6 {i6:g} vs {m[6]}; i9 {i9:g} vs {m[9]}; i10 {i10:g} vs {m[10]}; i11 {i11:g} vs {m[11]}")
        for i, v in ((5, i5), (6, i6)):
            if abs(v - m[i]) > 0.5:
                problem(f"{CODE} {q} i7 operand", f"operand item {i} of HEAD master {m[i]} != prior-period note {v}: item 7 would not be on the latest basis")
        for i, v in ((9, i9), (10, i10), (11, i11)):
            if abs(v - m[i]) > 0.5:
                NOTES.append(f"{q} item {i}: prior-period note {v:g} vs master {m[i]} (not loaded: outside the planned scope; item 8 and residual 12 unchanged)")

    # ---- single quarters: derived (cum(q) - cum(q-1)) vs the printed prior 3-month column
    adopted_cum = dict(plan_val)

    def cum_after(i, q):
        return adopted_cum.get((CODE, i, q), HM.get((CODE, i, q)))

    ITEM_LABELS = {1: ["보험영업손익"], 16: ["기타사업비용"], 17: ["투자영업손익", "보험금융손익"], 20: ["영업이익"], 21: ["영업외손익"], 22: ["법인세비용차감전순이익"], 23: ["법인세비용"],
                   24: ["당기순이익(손실)"], 25: ["기타포괄손익"], 26: ["기타포괄손익-공정가치측정채무상품평가손익"], 27: ["보험계약자산부채순금융손익"], 28: ["현금흐름위험회피파생상품평가손익"],
                   29: ["기타포괄손익-공정가치측정지분상품평가손익"], 30: ["재보험계약자산부채순금융손익"], 31: ["총포괄손익"]}
    n_s = n_s_bad = 0
    for q in ("2023.2Q", "2023.3Q"):
        st = stm[q]
        pq = f"{q[:4]}.{int(q[5]) - 1}Q"
        for i, labs in ITEM_LABELS.items():
            if cum_after(i, q) is None or cum_after(i, pq) is None:
                continue
            # item 17 in the Q2 / Q3 layout is the printed 투자영업손익 only (no separate 보험금융손익 section); in the Q1 layout 2023.1Q cum = 투자영업손익 + 보험금융손익 (checked above)
            labs_use = [labs[0]] if i == 17 else labs
            p3 = 0.0
            for lab in labs_use:
                v, _c = st.get(lab, 1, kind="3m")
                p3 += v
            D = cum_after(i, q) - cum_after(i, pq)
            n_s += 1
            if abs(D - p3) > 1.0001:
                n_s_bad += 1
                problem(f"{CODE} {q} i{i} single quarter", f"derived cum(q)-cum(q-1) {D} != printed prior 3-month {p3} (diff {D - p3:+.1f})")
        # item 32 single quarter = 25 - (26..30)
    txt.append(f"single-quarter check (2023.2Q / 2023.3Q derived vs printed prior 3-month column): {n_s} cells, outside +-1: {n_s_bad}")

    # ---- 2023.4Q single quarters that the builder derivation changes (cum4 unchanged, cum3 adopted)
    chg = []
    for i in range(1, 33):
        k4, k3 = (CODE, i, "2023.4Q"), (CODE, i, "2023.3Q")
        if k4 in HM and HM[k4] is not None and cum_after(i, "2023.3Q") is not None:
            new_d = HM[k4] - cum_after(i, "2023.3Q")
            old_d = HD.get(k4)
            if old_d is not None and abs(new_d - old_d) > 1e-9:
                chg.append((i, old_d, new_d))
    txt.append("2023.4Q single quarter (값_당분기 = master cum4 - adopted cum3) that changes: " + "; ".join(f"i{i} {o:g}->{n:g}" for i, o, n in chg))

    # ---- CSM cells
    n_c = n_c_ok = 0
    CSMQ = {}
    for cb in PLAN["csm_buckets"]:
        code, q = cb["code"], cb["quarter"]
        rel = cb["file"].split(" ")[0]
        CSMQ[q] = rel
        for c in cb["cells"]:
            n_c += 1
            where = f"{code} {q} CSM i{c['item']}"
            n_before = len(PROBLEMS)
            ho = CM.get((code, c["item"], q))
            if (ho is None) != (c["old"] is None) or (ho is not None and abs(ho - c["old"]) > 1e-9):
                problem(where, f"old {c['old']} != HEAD CSM master {ho}")
            if (code, c["item"], q) in GC:
                problem(where, "owner CSM gold exists at HEAD for a cell planned as new")
            exact = 0.0
            for p in c["parts"]:
                v = check_csm_part(p, c["item"], rel, where)
                exact += p["sign"] * parse_num(p["printed"]) / CSM_SCALE[p["unit"]]
            if abs(exact - c["exact"]) > 1e-4:
                problem(where, f"exact recomputed {exact} != plan {c['exact']}")
            if abs(round(exact, 1) - c["new"]) > 1e-9:
                problem(where, f"stored {c['new']} != round(exact,1) {round(exact, 1)}")
            if len(PROBLEMS) == n_before:
                n_c_ok += 1
        merged = [next((cc["new"] for cc in cb["cells"] if cc["item"] == i), cb["old"][i - 1]) for i in range(1, 7)]
        resid = merged[0] + merged[1] + merged[2] + merged[3] + merged[4] - merged[5]
        txt.append(f"CSM {q}: merged vector {merged}, closure residual {resid:+.2f}")
        if abs(resid) > 0.15:
            problem(f"{code} {q} CSM", f"closure residual {resid}")
    txt.append(f"CSM cells: {n_c}, all checks ok {n_c_ok}")

    # ---- PL4 <-> CSM5 pairing (independent)
    for cb in PLAN["csm_buckets"]:
        q = cb["quarter"]
        pl4 = plan_val.get((CODE, 4, q))
        c5 = next((c["new"] for c in cb["cells"] if c["item"] == 5), CM.get((CODE, 5, q)))
        txt.append(f"  pairing {q}: PL4 {pl4:g} mn = {pl4 / 100:.2f} eok vs |CSM5| {abs(c5):.1f} eok (diff {abs(pl4 / 100) - abs(c5):+.2f})")
        if abs(abs(pl4 / 100) - abs(c5)) > 0.06:
            problem(f"{CODE} {q} pairing", f"PL4 {pl4} vs CSM5 {c5}")

    # ---- merged-vector PL identities
    n_id = n_id_bad = 0
    for b in PLAN["buckets"]:
        code, q = b["code"], b["quarter"]
        v = {i: HM.get((code, i, q)) for i in range(1, 33)}
        for c in b["cells"]:
            v[c["item"]] = c["new"]
        S = lambda *xs: None if any(x is None for x in xs) else sum(xs)   # noqa: E731
        checks = [("20=1+17", v.get(20), S(v.get(1), v.get(17))), ("22=20+21", v.get(22), S(v.get(20), v.get(21))), ("31=24+25", v.get(31), S(v.get(24), v.get(25))),
                  ("17=18+19", v.get(17), S(v.get(18), v.get(19))), ("|22-24|=|23|", None if v.get(22) is None else abs(v[22] - v[24]), None if v.get(23) is None else abs(v[23]))]
        oci = [v[i] for i in (26, 27, 28, 29, 30, 32) if v.get(i) is not None]
        checks.append(("25=sum(OCI parts)", v.get(25), sum(oci) if oci else None))
        if None not in (v.get(3), v.get(4), v.get(5), v.get(6), v.get(7)):
            checks.append(("3=4+5+6+7", v[3], v[4] + v[5] + v[6] + v[7]))
        if None not in (v.get(8), v.get(9), v.get(10), v.get(11), v.get(12)):
            checks.append(("8=9+10+11+12", v[8], v[9] + v[10] + v[11] + v[12]))
        if None not in (v.get(2), v.get(3), v.get(8)):
            checks.append(("2=3+8", v[2], v[3] + v[8]))
        if None not in (v.get(1), v.get(2), v.get(15), v.get(16)):
            checks.append(("1=2+15-16 (LOB bridge)", v[1], v[2] + v[15] - v[16]))
        for name, l, r in checks:
            if l is None or r is None:
                continue
            n_id += 1
            ok = abs(l - r) <= 1.0001
            if not ok:
                n_id_bad += 1
                problem(f"{code} {q} identity", f"{name}: {l} vs {r} (resid {l - r:+.4f})")
            elif abs(l - r) > 1e-9:
                NOTES.append(f"{q} identity {name}: residual {l - r:+.1f} mn (rounding-level; cells of the 3 rounding-only differences stay at the master)")
    txt.append(f"identity checks on the merged vectors: {n_id}, outside +-1 mn: {n_id_bad}")

    # ---- contract vs plan vs HEAD
    pl_keys = set(plan_val)
    con_keys = {(e["code"], e["item"], e["quarter"]) for e in CON["gold_new"] + CON["gold_replace"]}
    if pl_keys != con_keys:
        problem("contract", f"contract cells != plan cells: only-plan {sorted(pl_keys - con_keys)[:5]} only-contract {sorted(con_keys - pl_keys)[:5]}")
    for e in CON["gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        if k in G:
            problem("contract", f"gold_new key {k} already in HEAD gold")
        if k not in HM:
            problem("contract", f"gold_new {k}: master row absent")
        if (HM.get(k) is None) != (e["was"] is None) or (HM.get(k) is not None and abs(HM[k] - e["was"]) > 5e-7):
            problem("contract", f"gold_new {k}: was {e['was']} != HEAD master {HM.get(k)}")
        if k in nd or (k[0], k[2], k[1]) in sd:
            problem("contract", f"gold_new {k}: a null_dangi / set_dangi pin exists at HEAD for the cell")
    for e in CON["csm_gold_new"]:
        k = (e["code"], e["item"], e["quarter"])
        if k in GC or k not in CM:
            problem("contract", f"csm_gold_new {k}: in HEAD CSM gold={k in GC}, in HEAD CSM master={k in CM}")
    if CON["gold_replace"] or CON["csm_gold_replace"] or CON["null_dangi_add"] or CON["set_dangi_add"] or CON["null_dangi_remove"] or CON["set_dangi_remove"] or CON["held"]:
        problem("contract", "contract is expected to hold only gold_new / csm_gold_new for KB라이프 D1-B")
    txt.append(f"contract: PL gold_new {len(CON['gold_new'])}, CSM gold_new {len(CON['csm_gold_new'])}, replace {len(CON['gold_replace'])}/{len(CON['csm_gold_replace'])}, dangi add/remove {len(CON['null_dangi_add'])}/{len(CON['set_dangi_add'])}/{len(CON['null_dangi_remove'])}/{len(CON['set_dangi_remove'])}, held {len(CON['held'])}")

    # ---- dropped (rounding-only) cells: re-read independently
    for b in PLAN["buckets"]:
        q = b["quarter"]
        st = stm[q]
        for d in b["dropped"]:
            # fresh re-read of the dropped (rounding-only) cell from the raw statement
            i = d["item"]
            if i == 16:
                fresh = st.get("기타사업비용", 1)[0]
            elif i == 29:
                fresh = st.get("기타포괄손익-공정가치측정지분상품평가손익", 1)[0]
            elif i == 18:
                g_ = lambda lab: st.get(lab, 1)[0]   # noqa: E731
                inv_ = g_("투자영업손익") + (g_("보험금융손익") if st.rows_by_label("보험금융손익") else 0.0)
                fin_ = (g_("보험금융수익") + g_("재보험금융수익")) - (g_("보험금융비용") + g_("재보험금융비용"))
                fresh = inv_ - fin_
            else:
                fresh = None
            txt.append(f"  dropped {q} i{d['item']}: master {d['old']} vs latest comparative {d['new']} (fresh raw re-read {fresh}) ({d['cls']}: {d['reason']})")
            if fresh is None or abs(fresh - d["new"]) > 1e-6:
                problem(f"{q} dropped i{d['item']}", f"fresh raw re-read {fresh} != plan comparative {d['new']}")
            if d["cls"] == "rounding" and abs(d["new"] - d["old"]) > 1.0001:
                problem(f"{q} dropped i{d['item']}", f"rounding-class drop with |diff| {abs(d['new'] - d['old'])} > 1")

    txt.append("notes:")
    for n in NOTES:
        txt.append("  " + n)
    txt.append(f"problems: {len(PROBLEMS)}")
    for p in PROBLEMS[:80]:
        txt.append("  " + json.dumps(p, ensure_ascii=False)[:500])
    (HERE / f"kr0099_verify{OUTTAG}.txt").write_text("\n".join(txt) + "\n", encoding="utf-8", newline="\n")
    (HERE / f"kr0099_verify{OUTTAG}.json").write_text(json.dumps(dict(problems=PROBLEMS, notes=NOTES), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\n".join(txt[:8]))
    print("...")
    print("\n".join(txt[-12:]))
    sys.exit(1 if PROBLEMS else 0)


if __name__ == "__main__":
    main()
