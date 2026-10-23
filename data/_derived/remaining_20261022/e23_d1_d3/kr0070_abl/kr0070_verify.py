# -*- coding: utf-8 -*-
"""KR0070 에이비엘생명보험 (ticket 20261023T0900Z, D3 = FY2023 2023.1Q-2023.4Q at the latest comparative, scenario N4_ABL_FY2023) -- INDEPENDENT re-read of EVERY planned cell.

Own code: imports only the standard library (no e21_* / e23_* / abl_lib / scripts / src module and NOT the planner), so it cannot share a defect with the planner.
The planner output (e23_plan_abl.json) is only COMPARED with what this script reads itself.

What it does
  A. CONTROL (proves the definitions): the ORIGINAL FY2023 filings (rcept 20230515002903 / 20230814002908 / 20231114002934 / 20240329001518), read with the same label definitions, are compared with the
     LIVE (pre-load) master.  2023.3Q / 2023.4Q: separate statement in the new layout.  2023.1Q / 2023.2Q: old layout (roman numerals); both the separate and the consolidated statement are read and the
     basis of the live value is reported (information, the load replaces it with the separate restated value).
  B. CANDIDATE: the FY2024 filings (rcept 20240516002045 / 20240814004092 / 20241114002738 / 20250331001358), separate 4-2 statement, the PRIOR-year cumulative column chosen by the dated period headers AND by
     the THEAD path, compared with the plan cell by cell (value, unit, sign, row label, physical line of every part).  CSM: separate-basis roll-forward 'prior' table, CSM column, rows by label.
  C. Statement-internal identities from freshly read printed cells; CSM roll-forward closure; PL4 (CSM amortisation) from THREE places (note (3), note (1), roll-forward) must agree; second CSM/statement source
     for the annual (audit report attachment _00760.xml).
  D. SEAM evidence: derived single quarters (cumulative differences) against the printed 3-month columns of the same restated filings; FY2025 annual third column (FY2023) vs the FY2024 prior column.
  E. Plan sanity: old values == live master, apply contract counts, owner-gold cells == the approved list.
Writes kr0070_verify.txt / kr0070_verify.json next to this file; exit code 1 when anything fails."""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / os.environ.get("KR0070_PLAN", "e23_plan_abl.json")).read_text(encoding="utf-8"))
MUTATE = os.environ.get("KR0070_MUTATE", "")      # '', 'col' (read the current column instead of the prior), 'line' (shift cited line), 'tbl' (take the 당기 CSM table), 'val' (alter a value), 'unit'
OUTTAG = os.environ.get("KR0070_OUTTAG", "")
BASE = Path(os.environ.get("KR0070_BASE", str(ROOT)))   # where the pre-load masters / gold files are read from (default: the repo root = before the load)
CODE = "KR0070"
TAG = re.compile(r"<[^>]+>")
_cache = {}
PROBLEMS = []
OUT = []
RES = {}

DART = "data/dart"
F = dict(
    N1="%s/FY2024_Q1/raw/KR0070_에이비엘생명보험/20240516002045.xml" % DART,
    N2="%s/FY2024_Q2/raw/KR0070_에이비엘생명보험/20240814004092.xml" % DART,
    N3="%s/FY2024_Q3/raw/KR0070_에이비엘생명보험/20241114002738.xml" % DART,
    N4="%s/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358/20250331001358.xml" % DART,
    N4AUD="%s/FY2024_Q4/raw/KR0070_에이비엘생명보험_20250331001358/20250331001358_00760.xml" % DART,
    O1="%s/FY2023_Q1/raw/KR0070_에이비엘생명보험/xml/20230515002903.xml" % DART,
    O2="%s/FY2023_Q2/raw/KR0070_에이비엘생명보험/xml/20230814002908.xml" % DART,
    O3="%s/FY2023_Q3/raw/KR0070_에이비엘생명보험/xml/20231114002934.xml" % DART,
    O4="%s/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518/xml/20240329001518.xml" % DART,
    O4AUD="%s/FY2023_Q4/raw/KR0070_에이비엘생명보험_20240329001518/xml/20240329001518_00760.xml" % DART,
    A25="%s/FY2025_Q4/raw/KR0070_에이비엘생명보험_20260331003080/20260331003080.xml" % DART,
)
QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
NEWKEY = {"2023.1Q": "N1", "2023.2Q": "N2", "2023.3Q": "N3", "2023.4Q": "N4"}
OLDKEY = {"2023.1Q": "O1", "2023.2Q": "O2", "2023.3Q": "O3", "2023.4Q": "O4"}
APPROVED_PL_GOLD = {("2023.1Q", 4)}
APPROVED_CSM_GOLD = {("2023.4Q", 1), ("2023.4Q", 4)}


def say(s=""):
    OUT.append(s)
    print(s)


def problem(where, msg):
    PROBLEMS.append(dict(where=where, problem=msg))
    say(f"  !! PROBLEM [{where}] {msg}")


def lines_of(rel):
    if rel not in _cache:
        _cache[rel] = (ROOT / rel).read_text(encoding="utf-8", errors="replace").split("\n")
    return _cache[rel]


def clean(s):
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("\u3000", " ").replace("\xa0", " ")).strip()


def nspace(s):
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


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


def sha12(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:12]


# ------------------------------------------------------------------------------------------------ raw table machinery (independent implementation)
def parse_tr(L, i, j):
    """cells of the TR spanning physical lines i..j (0-based inclusive): [dict(tag, colspan, rowspan, text, line)]  (blank cells included; line = physical line of the first text)"""
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            attrs = m.group(2)
            cs = re.search(r'COLSPAN="(\d+)"', attrs, re.I)
            rs = re.search(r'ROWSPAN="(\d+)"', attrs, re.I)
            rest = m.group(3)
            base = dict(tag=m.group(1).upper(), colspan=int(cs.group(1)) if cs else 1, rowspan=int(rs.group(1)) if rs else 1)
            if re.search(r"</(TD|TE|TH)>\s*$", rest, re.I):
                out.append(dict(base, text=clean(rest), line=k + 1))
            else:
                buf, tl, q = ([clean(rest)] if clean(rest) else []), (k + 1 if clean(rest) else None), k + 1
                while q <= j and not re.match(r"\s*</(TD|TE|TH)", L[q], re.I):
                    t = clean(L[q])
                    if t:
                        buf.append(t)
                        if tl is None:
                            tl = q + 1
                    q += 1
                out.append(dict(base, text=" ".join(buf).strip(), line=tl or (k + 1)))
                k = q
        k += 1
    return out


def table_rows(L, a, b):
    """all <TR> of the table spanning lines a..b (0-based): [dict(tr, cells)]"""
    rows, k = [], a
    while k <= b:
        if re.match(r"\s*<TR\b", L[k], re.I):
            j = k
            while not re.match(r"\s*</TR", L[j], re.I):
                j += 1
            rows.append(dict(tr=k + 1, cells=parse_tr(L, k, j)))
            k = j
        k += 1
    return rows


def all_tables(L):
    """[(a, b)] 0-based inclusive bounds of every LEAF <TABLE>...</TABLE> (tables that contain another table are skipped)"""
    out, stack = [], []
    for k, s in enumerate(L):
        if re.match(r"\s*<TABLE\b", s, re.I):
            if stack:
                stack[-1][1] = True
            stack.append([k, False])
        elif re.match(r"\s*</TABLE", s, re.I) and stack:
            a, has_child = stack.pop()
            if not has_child:
                out.append((a, k))
    return out


def header_paths(L, a, b):
    """logical column index -> header path (texts top to bottom, consecutive repeats removed) from the THEAD of the table a..b"""
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


def body_rows(L, a, b):
    """rows after </THEAD> (or all rows when there is no THEAD)"""
    h1 = next((k for k in range(a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), None)
    rows = table_rows(L, a, b)
    return [r for r in rows if h1 is None or r["tr"] - 1 > h1]


def titles(L):
    return [(k, clean(s)) for k, s in enumerate(L) if s.startswith("<TITLE")]


def section(L, title_re, nth=0):
    """(a, b) 0-based: from the nth <TITLE> matching title_re to the next <TITLE> of ANY kind"""
    ts = titles(L)
    hits = [n for n, (k, t) in enumerate(ts) if re.search(title_re, t)]
    if len(hits) <= nth:
        raise RuntimeError(f"title {title_re!r} (#{nth}) not found")
    n = hits[nth]
    return ts[n][0], (ts[n + 1][0] if n + 1 < len(ts) else len(L) - 1)


def unit_above(L, ln, span=400):
    """'(단위 : 원|백만원|천원)' nearest above 1-based line ln"""
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


UNIT_MN = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0}


def mn(printed, unit):
    v = parse_num(printed)
    return None if v is None else v * UNIT_MN[unit]


def close(a, b, tol=2e-6):
    return a is not None and b is not None and abs(a - b) <= tol


# ------------------------------------------------------------------------------------------------ statement (separate, new layout 4-2.)
LABELS = {   # item key -> normalised row label (spaces removed); exactly one row of the statement must carry it
    "ins_result": "보험손익", "rev": "보험수익", "rerev": "재보험수익", "cost": "보험비용", "recost": "재보험비용", "other_cost": "기타사업비용", "inv": "투자손익",
    "ins_fin_rev": "보험금융수익", "reins_fin_rev": "재보험금융수익", "ins_fin_cost": "보험금융비용", "reins_fin_cost": "재보험금융비용", "op": "영업이익(손실)", "nonop": "영업외손익",
    "pretax": "법인세차감전순이익", "tax": "법인세비용(수익)", "ni": "당기순이익(손실)", "oci": "기타포괄손익", "oci_fvoci": "기타포괄손익-공정가치측정금융자산평가손익",
    "oci_insfin": "보험계약자산(부채)순금융손익", "oci_hedge": "현금흐름위험회피파생상품평가손익", "oci_reinsfin": "재보험계약자산(부채)순금융손익", "tci": "총포괄손익",
    "oci_credit": "기타포괄손익-공정가치측정신용손실",
}
OCI_LEAVES = ["oci_fvoci", "oci_credit", "oci_insfin", "oci_reinsfin", "oci_hedge"]
PERIOD_RE = re.compile(r"제\s*(\d+)\s*기\s*(?:(1분기|반기|3분기)\s*)?(\d{4})\.(\d{2})\.(\d{2})\s*부터\s*(\d{4})\.(\d{2})\.(\d{2})\s*까지")


class Stmt:
    """separate '4-2. 포괄손익계산서' of one filing (new layout): dated period list, THEAD paths, rows with ALL value cells.  Columns are chosen by the DATED period header (not by position)."""

    def __init__(self, key, sec_re=r"^4-2\.\s*포괄손익계산서"):
        self.key, self.rel = key, F[key]
        L = self.L = lines_of(self.rel)
        a, b = self.sec = section(L, sec_re)
        # the statement table: first leaf table of the section that has a THEAD and rows 보험손익 + 법인세차감전순이익
        self.tab = None
        for (ta, tb) in all_tables(L):
            if not (a <= ta <= b):
                continue
            labs = {nspace(r["cells"][0]["text"]) for r in table_rows(L, ta, tb) if r["cells"]}
            if "보험손익" in labs and "법인세차감전순이익" in labs:
                self.tab = (ta, tb)
                break
        if self.tab is None:
            raise RuntimeError(f"{self.rel}: statement table not found in section {a + 1}..{b + 1}")
        ta, tb = self.tab
        self.periods = {}
        for k in range(a, ta):
            m = PERIOD_RE.search(clean(L[k]))
            if m and "<TE" in "".join(L[max(k - 3, 0):k + 1]):
                self.periods[int(m.group(1))] = dict(line=k + 1, text=clean(L[k]), start=f"{m.group(3)}.{m.group(4)}.{m.group(5)}", end=f"{m.group(6)}.{m.group(7)}.{m.group(8)}")
        un, unl = unit_above(L, ta + 1, span=200)
        if un is None:
            un, unl = unit_above(L, ta + 40, span=300)
        self.unit, self.unit_line = un, unl
        self.paths = header_paths(L, ta, tb)
        self.rows = body_rows(L, ta, tb)

    def col(self, year, kind="cum"):
        """logical column index whose dated period ENDS in `year`; kind 'cum' = the cumulative (누적) column of a quarterly table or the only column of an annual table, '3m' = 3개월 column"""
        cands = []
        for j, p in enumerate(self.paths):
            if j == 0 or not p:
                continue
            m = re.search(r"제\s*(\d+)\s*기", p[0])
            if not m:
                continue
            per = self.periods.get(int(m.group(1)))
            if per is None or not per["end"].startswith(f"{year}."):
                continue
            tail = p[1] if len(p) > 1 else None
            if kind == "cum" and tail in (None, "누적"):
                cands.append(j)
            elif kind == "3m" and tail == "3개월":
                cands.append(j)
        if len(cands) != 1:
            raise RuntimeError(f"{self.rel}: {len(cands)} columns for year {year} kind {kind}: {cands}; paths {self.paths}")
        return cands[0]

    def row(self, label_key):
        want = nspace(LABELS[label_key])
        hits = [r for r in self.rows if r["cells"] and nspace(r["cells"][0]["text"]) == want]
        if len(hits) != 1:
            raise RuntimeError(f"{self.rel}: {len(hits)} rows labelled {LABELS[label_key]!r}")
        return hits[0]

    def cell(self, label_key, year, kind="cum"):
        j = self.col(year, kind)
        r = self.row(label_key)
        cs = r["cells"]
        if len(cs) != len(self.paths):
            raise RuntimeError(f"{self.rel}: row {LABELS[label_key]!r} has {len(cs)} cells, header {len(self.paths)}")
        c = cs[j]
        v = mn(c["text"], self.unit)
        if v is None:
            raise RuntimeError(f"{self.rel}: {LABELS[label_key]!r} col {j} not numeric {c['text']!r}")
        return dict(label=cs[0]["text"], label_line=cs[0]["line"], printed=c["text"], line=c["line"], unit=self.unit, mn=v, col=j, header=self.paths[j])


def stmt_vector(S, year, kind="cum"):
    """freshly read printed cells of the statement -> {key: cell}"""
    return {k: S.cell(k, year, kind) for k in LABELS}


def items_from(V):
    """PL items (백만원) from the read cells, by the production definitions: 3 = 보험수익 - 보험비용, 8 = 재보험수익 - 재보험비용, 2 = 3 + 8, 19 = 보험금융수익 계열 - 보험금융비용 계열, 18 = 17 - 19"""
    g = {k: V[k]["mn"] for k in V}
    it = {1: g["ins_result"], 16: g["other_cost"], 17: g["inv"], 20: g["op"], 21: g["nonop"], 22: g["pretax"], 23: g["tax"], 24: g["ni"], 25: g["oci"], 26: g["oci_fvoci"],
          27: g["oci_insfin"], 28: g["oci_hedge"], 30: g["oci_reinsfin"], 31: g["tci"], 32: g["oci_credit"]}
    it[3] = g["rev"] - g["cost"]
    it[8] = g["rerev"] - g["recost"]
    it[2] = it[3] + it[8]
    it[19] = (g["ins_fin_rev"] + g["reins_fin_rev"]) - (g["ins_fin_cost"] + g["reins_fin_cost"])
    it[18] = it[17] - it[19]
    return it


def identities(V, tol=2e-6):
    """statement-internal identities from PRINTED cells (백만원)"""
    g = {k: V[k]["mn"] for k in V}
    out = []

    def chk(name, lhs, rhs):
        out.append((name, lhs - rhs, abs(lhs - rhs) <= tol))

    chk("보험손익 = 보험수익+재보험수익-보험비용-재보험비용-기타사업비용", g["ins_result"], g["rev"] + g["rerev"] - g["cost"] - g["recost"] - g["other_cost"])
    chk("영업이익 = 보험손익+투자손익", g["op"], g["ins_result"] + g["inv"])
    chk("세전이익 = 영업이익+영업외손익", g["pretax"], g["op"] + g["nonop"])
    chk("당기순이익 = 세전-법인세", g["ni"], g["pretax"] - g["tax"])
    chk("총포괄손익 = 당기순이익+기타포괄손익", g["tci"], g["ni"] + g["oci"])
    chk("기타포괄손익 = 5개 구성요소 합", g["oci"], sum(g[k] for k in OCI_LEAVES))
    return out


# ------------------------------------------------------------------------------------------------ Stmt: label alternatives (old vintage) and old-layout (roman numeral) statements
LABEL_ALTS = {
    "oci_fvoci": ["기타포괄손익-공정가치측정금융자산평가손익", "기타포괄손익-공정가치측정금융자산관련손익"],
    "tax": ["법인세비용(수익)", "법인세비용"],
}
OPTIONAL = {"other_cost"}


def _labels(key):
    return [nspace(x) for x in LABEL_ALTS.get(key, [LABELS[key]])]


def _row(self, label_key, optional=False):
    want = set(_labels(label_key))
    hits = [r for r in self.rows if r["cells"] and nspace(r["cells"][0]["text"]) in want]
    if len(hits) == 0 and optional:
        return None
    if len(hits) != 1:
        raise RuntimeError(f"{self.rel}: {len(hits)} rows labelled {sorted(want)}")
    return hits[0]


def _cell(self, label_key, year, kind="cum"):
    j = self.col(year, kind)
    r = self.row(label_key, optional=label_key in OPTIONAL)
    if r is None:
        return None
    cs = r["cells"]
    if len(cs) != len(self.paths):
        raise RuntimeError(f"{self.rel}: row {cs[0]['text']!r} has {len(cs)} cells, header {len(self.paths)}")
    c = cs[j]
    v = mn(c["text"], self.unit)
    if v is None:
        raise RuntimeError(f"{self.rel}: {cs[0]['text']!r} col {j} not numeric {c['text']!r}")
    return dict(label=cs[0]["text"], label_line=cs[0]["line"], printed=c["text"], line=c["line"], unit=self.unit, mn=v, col=j, header=self.paths[j])


Stmt.row = _row
Stmt.cell = _cell


def stmt_vector(S, year, kind="cum"):                                      # noqa: F811  (optional rows may be absent in the old vintage)
    out = {}
    for k in LABELS:
        c = S.cell(k, year, kind)
        if c is not None:
            out[k] = c
    return out


def items_from(V, absolute_costs=False):                                   # noqa: F811
    """PL items (백만원), production definitions: 3 = 보험수익 - 보험비용, 8 = 재보험수익 - 재보험비용, 2 = 3 + 8, 19 = (보험금융수익 + 재보험금융수익) - (보험금융비용 + 재보험금융비용), 18 = 17 - 19;
    absolute_costs: the old vintage prints costs in parentheses (negative) -> magnitude"""
    g = {k: V[k]["mn"] for k in V}
    c = (lambda x: abs(x)) if absolute_costs else (lambda x: x)
    it = {1: g["ins_result"], 17: g["inv"], 20: g["op"], 21: g["nonop"], 22: g["pretax"], 23: c(g["tax"]) if absolute_costs else g["tax"], 24: g["ni"], 25: g["oci"], 26: g["oci_fvoci"],
          27: g["oci_insfin"], 28: g["oci_hedge"], 30: g["oci_reinsfin"], 31: g["tci"], 32: g["oci_credit"]}
    if "other_cost" in g:
        it[16] = g["other_cost"]
    it[3] = g["rev"] - c(g["cost"])
    it[8] = g["rerev"] - c(g["recost"])
    it[2] = it[3] + it[8]
    it[19] = (g["ins_fin_rev"] + g["reins_fin_rev"]) - (c(g["ins_fin_cost"]) + c(g["reins_fin_cost"]))
    it[18] = it[17] - it[19]
    return it


def strip_ju(s):
    return re.sub(r"\(주[^)]*\)", "", s)


def core_label(s):
    """row label without leading roman numeral / (n) / n. markers and (주..) footnotes, spaces removed"""
    s = nspace(strip_ju(s))
    s = re.sub(r"^([IVX]+\.|\(\d+\)|\d+\.)", "", s)
    return s


class OldStmt:
    """old-layout (roman numeral, subtotal columns) statement of the ORIGINAL 2023.1Q / 2023.2Q filings: header '과 목 | 당 | 전', every period spans 2 cells (detail | subtotal) per 3개월/누적 slot."""

    def __init__(self, key, sec_re):
        self.key, self.rel = key, F[key]
        L = self.L = lines_of(self.rel)
        a, b = section(L, sec_re)
        self.tab = None
        for (ta, tb) in all_tables(L):
            if not (a <= ta <= b):
                continue
            rows = table_rows(L, ta, tb)
            labs = {core_label(r["cells"][0]["text"]) for r in rows if r["cells"]}
            if "보험서비스결과" in labs and "법인세비용차감전순이익" in labs:
                self.tab = (ta, tb, rows)
                break
        if self.tab is None:
            raise RuntimeError(f"{self.rel}: old-layout statement not found in {sec_re}")
        ta, tb, rows = self.tab
        self.unit, self.unit_line = unit_above(L, ta + 1, span=200)
        self.rows = [r for r in rows if r["cells"] and r["cells"][0]["tag"] in ("TE", "TD") and len(r["cells"]) > 4]

    def slots(self, label_core):
        hits = [r for r in self.rows if core_label(r["cells"][0]["text"]) == label_core]
        if len(hits) != 1:
            raise RuntimeError(f"{self.rel}: {len(hits)} old-layout rows {label_core!r}")
        cs = hits[0]["cells"][1:]
        out = []
        for k in range(0, len(cs) - 1, 2):
            a, b = cs[k], cs[k + 1]
            c = a if a["text"] != "" else b
            out.append(dict(printed=c["text"], line=c["line"], mn=mn(c["text"], self.unit) if c["text"] != "" else None))
        return out


def summary_pl(key, which):
    """'1. 요약재무정보' summary income statement, which = '연결' | '별도': first value column (current period).  rows -> {core label: dict(printed, line, mn)}"""
    L = lines_of(F[key])
    a, b = section(L, r"^1\.\s*요약재무정보")
    out = None
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = table_rows(L, ta, tb)
        labs = {core_label(r["cells"][0]["text"]) for r in rows if r["cells"]}
        if not ({"보험서비스결과", "영업이익", "법인세비용차감전순이익"} <= labs):
            continue
        ctx = ""
        for k in range(ta - 1, max(ta - 40, 0), -1):
            ctx += clean(L[k]) + " "
        tag = "요약연결" if "요약연결" in ctx[:200] else ("요약별도" if "요약별도" in ctx[:200] else None)
        if tag != "요약" + which:
            continue
        un, _ = unit_above(L, ta + 1, span=120)
        out = {}
        for r in rows:
            cs = r["cells"]
            if len(cs) >= 2 and cs[0]["tag"] in ("TE", "TD"):
                v = mn(cs[1]["text"], un)
                if v is not None:
                    out[core_label(cs[0]["text"])] = dict(printed=cs[1]["text"], line=cs[1]["line"], mn=v)
        break
    if out is None:
        raise RuntimeError(f"{F[key]}: summary income statement ({which}) not found")
    return out


# ------------------------------------------------------------------------------------------------ notes: PL4 (CSM amortisation) from three places, CSM roll-forward
def notes_range(L):
    return section(L, r"^5\.\s*재무제표 주석")


def numeric_cells(r):
    return [(c["text"], c["line"], parse_num(c["text"])) for c in r["cells"][1:] if parse_num(c["text"]) is not None and c["text"] != ""]


def pl4_note3(key, which="prior"):
    """note (3) '잔여보장요소 및 현금흐름 회수 관련 보험료 배분액' of the ISSUED contracts (row 해당 기간 동안 발생한 보험서비스비용), row 해당 기간에 서비스의 이전으로 당기손익에 인식한 보험계약마진 금액"""
    L = lines_of(F[key])
    a, b = notes_range(L)
    want = nspace("해당 기간에 서비스의 이전으로 당기손익에 인식한 보험계약마진 금액")
    iss = nspace("해당 기간 동안 발생한 보험서비스비용")
    hits = []
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = table_rows(L, ta, tb)
        labs = [nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if want in labs and iss in labs:
            hits.append((ta, tb, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{F[key]}: {len(hits)} issued (3) tables with the CSM release row")
    ta, tb, rows = hits[0]
    un, _ = unit_above(L, ta + 1, span=120)
    hdr = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "구분")
    heads = [c["text"] for c in hdr["cells"][1:]]
    j = next(i for i, h in enumerate(heads) if h.startswith("전" if which == "prior" else "당"))
    row = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == want)
    c = row["cells"][1 + j]
    return dict(printed=c["text"], line=c["line"], unit=un, mn=mn(c["text"], un), table=(ta + 1, tb + 1), heads=heads, label=row["cells"][0]["text"], label_line=row["cells"][0]["line"])


def pl4_note1(key):
    """note (1) 보험영업수익 table (rows 예상보험금 + 보험계약마진상각 + 보험수익): LAST numeric cell of the 보험계약마진상각 row = prior-period cumulative"""
    L = lines_of(F[key])
    a, b = notes_range(L)
    hits = []
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = table_rows(L, ta, tb)
        labs = [nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if "보험계약마진상각" in labs and "예상보험금" in labs and "보험수익" in labs and "발생재보험금" in labs:
            hits.append((ta, tb, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{F[key]}: {len(hits)} (1) 보험영업수익 tables")
    ta, tb, rows = hits[0]
    un, _ = unit_above(L, ta + 1, span=120)
    row = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "보험계약마진상각")
    nums = numeric_cells(row)
    t, ln, v = nums[-1]
    return dict(printed=t, line=ln, unit=un, mn=mn(t, un), table=(ta + 1, tb + 1), n_numeric=len(nums), label=row["cells"][0]["text"], label_line=row["cells"][0]["line"])


CAPTION_RE = re.compile(r"^([12])\)\s*(당|전)(분기|반기|기)$")
CSM_CORE = {
    1: lambda c: c == "기초보험계약순부채",
    2: lambda c: c == "해당기간에처음인식한계약의효과",
    3: lambda c: c in ("보험금융비용", "보험금융비용(수익)"),
    4: lambda c: c == "보험계약마진을조정하는추정치의변동분",
    5: lambda c: c == "서비스제공으로당기손익으로인식된보험계약마진",
    6: lambda c: re.match(r"^(분기말|반기말|기말)보험계약순부채", c) is not None,
}


def caption_role(L, ta):
    """'cur' | 'prior' from the nearest text line above the table that is exactly '1) 당분기' / '2) 전분기' (반기, 기)"""
    n = 0
    for k in range(ta - 1, max(ta - 400, 0), -1):
        t = clean(L[k])
        if not t:
            continue
        n += 1
        m = CAPTION_RE.match(t)
        if m:
            return ("cur" if m.group(2) == "당" else "prior"), k + 1, t
        if n > 40:
            break
    return None, None, None


def csm_tables(rel, lo=None, hi=None, sec_re=r"^5\.\s*재무제표 주석"):
    """CSM roll-forward tables of the ISSUED contracts (header has 보험계약마진, row 기초 보험계약순부채): {role: dict(rows, table, caption, unit, col)}"""
    L = lines_of(rel)
    if lo is None:
        lo, hi = section(L, sec_re)
    out = {}
    for (ta, tb) in all_tables(L):
        if not (lo <= ta <= hi):
            continue
        paths = header_paths(L, ta, tb)
        if not paths:
            continue
        jcsm = [j for j, p in enumerate(paths) if p and p[-1] == "보험계약마진"]
        if len(jcsm) != 1:
            continue
        rows = body_rows(L, ta, tb)
        cores = [core_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if "기초보험계약순부채" not in cores:
            continue
        role, cl, ct = caption_role(L, ta)
        un, _ = unit_above(L, ta + 1, span=120)
        if role in out:
            raise RuntimeError(f"{rel}: two CSM tables with role {role}: {out[role]['table']} and {(ta + 1, tb + 1)}")
        res = {}
        for item, f in CSM_CORE.items():
            hit = [r for r in rows if r["cells"] and f(core_label(r["cells"][0]["text"]))]
            if len(hit) != 1:
                res[item] = None
                continue
            r = hit[0]
            if len(r["cells"]) != len(paths):
                raise RuntimeError(f"{rel}: CSM row {r['cells'][0]['text']!r} has {len(r['cells'])} cells, header {len(paths)}")
            c = r["cells"][jcsm[0]]
            res[item] = dict(label=r["cells"][0]["text"], label_line=r["cells"][0]["line"], printed=c["text"], line=c["line"], mn=(mn(c["text"], un) if c["text"] not in ("",) else None))
        out[role] = dict(rows=res, table=(ta + 1, tb + 1), caption=(cl, ct), unit=un, col=jcsm[0])
    return out


RESTATE_MAP = [("보험손익", 1), ("투자손익", 17), ("영업이익", 20), ("영업손익", 20), ("영업외손익", 21), ("법인세비용차감전순이익", 22), ("법인세비용차감전순손익", 22), ("법인세비용", 23),
               ("분기순이익", 24), ("반기순이익", 24), ("당기순손익", 24), ("당기순이익", 24), ("기타포괄손익", 25), ("총포괄손익", 31), ("총포괄이익", 31)]


def restate_table(key):
    """the issuer's own '재작성에 따른 비교표시 포괄손익계산서의 변경효과' table (separate FS notes): {item: (before, after, printed_before, printed_after, line_before, line_after)} in 백만원"""
    L = lines_of(F[key])
    a, b = notes_range(L)
    hits = []
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = table_rows(L, ta, tb)
        texts = [c["text"] for r in rows for c in r["cells"]]
        if not (("조정전" in texts and "조정후" in texts) or ("변경전" in texts and "변경후" in texts)):
            continue
        cores = {core_label(r["cells"][0]["text"]) for r in rows if r["cells"]}
        if "보험손익" in cores and "투자손익" in cores:
            hits.append((ta, tb, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{F[key]}: {len(hits)} issuer restatement tables in the separate notes")
    ta, tb, rows = hits[0]
    un, _ = unit_above(L, ta + 1, span=120)
    out = {}
    for r in rows:
        cs = r["cells"]
        if len(cs) != 3 or cs[0]["tag"] not in ("TE", "TD"):
            continue
        core = core_label(cs[0]["text"])
        for name, item in RESTATE_MAP:
            if core == name:
                out[item] = dict(before=mn(cs[1]["text"], un), after=mn(cs[2]["text"], un), pb=cs[1]["text"], pa=cs[2]["text"], lb=cs[1]["line"], la=cs[2]["line"], label=cs[0]["text"])
                break
    out["_table"] = (ta + 1, tb + 1)
    return out


def load_masters(base):
    pl = json.loads((base / "PL_breakdown.json").read_text(encoding="utf-8"))
    cs = json.loads((base / "CSM_waterfall.json").read_text(encoding="utf-8"))
    gold = json.loads((base / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
    cgold = json.loads((base / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
    return pl, cs, gold, cgold


def label_key(label):
    n = nspace(label)
    for k in LABELS:
        if n in _labels(k):
            return k
    return None


# ------------------------------------------------------------------------------------------------ main
def main():
    pl_rows, csm_rows, gold, cgold = load_masters(BASE)
    LIVE = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_rows}
    LIVEC = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_rows}
    GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GOLDC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in cgold["set"]}
    say(f"KR0070 independent re-read | plan {PLAN.get('scenario')} | masters from {BASE} | mutation '{MUTATE}'")
    say("input hashes: " + ", ".join(f"{k}={sha12(v)}" for k, v in F.items() if (ROOT / v).exists()))

    # ---------------------------------------------------------------- B. candidate re-read (new filings, separate statement, prior-year cumulative)
    say("\n== B. CANDIDATE: FY2024 filings, separate 4-2 statement, prior-year (2023) cumulative column, read with the production definitions")
    NEW = {}
    year = 2024 if MUTATE == "col" else 2023
    for q in QUARTERS:
        S = Stmt(NEWKEY[q])
        vec = stmt_vector(S, year, "cum")
        it = items_from(vec)
        n3 = pl4_note3(NEWKEY[q], "cur" if MUTATE == "col" else "prior")
        n1 = pl4_note1(NEWKEY[q])
        rt = restate_table(NEWKEY[q])
        NEW[q] = dict(S=S, vec=vec, items=it, n3=n3, n1=n1, rt=rt)
        hdr = vec["ins_result"]["header"]
        ordinal = int(re.search(r"제\s*(\d+)", hdr[0]).group(1))
        ptxt = S.periods[ordinal]["text"]
        say(f"  {q}: {S.rel} | unit {S.unit} (line {S.unit_line}) | column {vec['ins_result']['col']} header {hdr} | period header (L{S.periods[ordinal]['line']}) {ptxt}")
        it[4] = n3["mn"]                                  # item 4 = CSM amortisation (note (3), prior-period cumulative); note (1) and the roll-forward must agree (checked below)
    say("  PL4 (CSM amortisation, 백만원) per quarter: note (3) prior | note (1) prior cumulative | CSM roll-forward row 5 (see below)")

    # CSM tables (new filings): prior role (or cur role under the 'tbl' mutation)
    CSMN = {}
    for q in QUARTERS:
        T = csm_tables(F[NEWKEY[q]])
        role = "cur" if MUTATE == "tbl" else "prior"
        if role not in T or ("cur" not in T) or len(T) != 2:
            problem(f"{q} CSM", f"expected exactly one cur and one prior CSM table, got {sorted(T)}")
        CSMN[q] = T[role]
    for q in QUARTERS:
        n3, n1 = NEW[q]["n3"], NEW[q]["n1"]
        c5 = -CSMN[q]["rows"][5]["mn"]
        ok = (n3["mn"] == n1["mn"] == c5)
        say(f"    {q}: note3 {n3['printed']} (L{n3['line']}) | note1 {n1['printed']} (L{n1['line']}, {n1['n_numeric']} numeric cells, last) | roll-forward row 5 {CSMN[q]['rows'][5]['printed']} (L{CSMN[q]['rows'][5]['line']}) -> {'AGREE' if ok else 'DISAGREE'}")
        if not ok:
            problem(f"{q} PL4", "CSM amortisation differs between note (3), note (1) and the roll-forward")

    # ---------------------------------------------------------------- B1. PL cells vs plan
    say("\n== B1. every planned PL cell: value, unit, sign, row label, physical line of each part")
    n_ok = n_cells = 0
    plan_pl = {}
    for b in PLAN["buckets"]:
        q = b["quarter"]
        mine = NEW[q]["items"]
        vec = NEW[q]["vec"]
        S = NEW[q]["S"]
        if b["meta"]["file"] != F[NEWKEY[q]]:
            problem(f"{q}", f"plan source file {b['meta']['file']} != {F[NEWKEY[q]]}")
        for c in b["cells"]:
            n_cells += 1
            item = c["item"]
            plan_pl[(q, item)] = c
            mv = mine.get(item)
            pv = c["new"]
            if MUTATE == "val" and q == "2023.2Q" and item == 20:
                pv += 1.0
            ok = close(mv, pv, 2e-6)
            msgs = []
            if not ok:
                msgs.append(f"value plan {pv} != re-read {mv}")
            # unit
            if c["unit"] != "백만원":
                msgs.append(f"unit {c['unit']}")
            # parts
            tot = 0.0
            for p in c["parts"]:
                ln = p["line"] + (1 if MUTATE == "line" and q == "2023.1Q" and item == 1 else 0)
                if item == 4:
                    ref = NEW[q]["n1"]
                    if not (ln == ref["line"] and p["printed"] == ref["printed"] and p["unit"] == ref["unit"]):
                        msgs.append(f"PL4 part L{ln} {p['printed']} {p['unit']} != note (1) L{ref['line']} {ref['printed']} {ref['unit']}")
                    if not close(p["contribution_mn"], ref["mn"]):
                        msgs.append("PL4 contribution")
                    tot += p["contribution_mn"]
                    continue
                k = label_key(p["label"])
                if k is None:
                    msgs.append(f"unknown part label {p['label']!r}")
                    continue
                mc = vec[k]
                if mc["label"] and nspace(mc["label"]) != nspace(p["label"]):
                    msgs.append(f"label {p['label']!r} != {mc['label']!r}")
                if ln != mc["line"]:
                    msgs.append(f"part {p['label']} line {ln} != re-read L{mc['line']}")
                if p["printed"] != mc["printed"]:
                    msgs.append(f"part {p['label']} printed {p['printed']} != {mc['printed']}")
                if p["unit"] != mc["unit"]:
                    msgs.append(f"part {p['label']} unit {p['unit']} != {mc['unit']}")
                expect = p["sign"] * (abs(mc["mn"]) if p["abs"] else mc["mn"])
                if not close(p["contribution_mn"], expect):
                    msgs.append(f"part {p['label']} contribution {p['contribution_mn']} != sign*{'|x|' if p['abs'] else 'x'} {expect}")
                tot += p["contribution_mn"]
            for o in c.get("operands", []):
                lv = LIVE.get((CODE, o["item"], q))
                if lv is None or not close(lv["값"], o["value"]) or not close(mine.get(o["item"]), o["value"], 2e-6):
                    msgs.append(f"operand item {o['item']} {o['value']}: live {None if lv is None else lv['값']} / re-read {mine.get(o['item'])}")
                tot += o["sign"] * o["value"]
            if c["parts"] and not close(tot, pv, 5e-6):
                msgs.append(f"sum of parts+operands {tot} != cell {pv}")
            if msgs:
                problem(f"{q} i{item}", "; ".join(msgs))
            else:
                n_ok += 1
    say(f"  planned PL cells {n_cells}, fully matching the independent re-read: {n_ok}")
    RES["pl_cells"] = n_cells
    RES["pl_cells_ok"] = n_ok

    # ---------------------------------------------------------------- B2. completeness: every other re-read item must equal the live master (else the plan skipped a change)
    say("\n== B2. completeness: items re-read from the filing but NOT in the plan (live master vs re-read)")
    SKIP_NOTE = {}
    for q in QUARTERS:
        for item in sorted(NEW[q]["items"]):
            if (q, item) in plan_pl:
                continue
            lv = LIVE.get((CODE, item, q))
            lvv = None if lv is None else lv["값"]
            mv = NEW[q]["items"][item]
            if lvv is None:
                problem(f"{q} i{item}", f"re-read value {mv} but the live master is blank and the plan skips it (fill missing)")
                continue
            d = mv - lvv
            cls = "equal" if abs(d) <= 2e-5 else ("rounding" if abs(d) <= 1.0001 else "DIFFERENT")
            SKIP_NOTE[(q, item)] = (lvv, mv, cls)
            say(f"  {q} i{item:>2}: live {lvv:>16,.6f} re-read {mv:>16,.6f} diff {d:+.6f} -> {cls}")
            if cls == "DIFFERENT":
                problem(f"{q} i{item}", f"not in the plan but live {lvv} != re-read {mv}")

    # ---------------------------------------------------------------- B3. issuer's own restatement table (변경전/변경후, separate FS notes)
    say("\n== B3. the issuer's own restatement table (separate FS notes): 변경후 == planned new (rounded to 백만원), 변경전 vs the old vintage")
    for q in QUARTERS:
        rt = NEW[q]["rt"]
        say(f"  {q}: table L{rt['_table'][0]}-{rt['_table'][1]}")
        for item in sorted(k for k in rt if k != "_table"):
            r = rt[item]
            mv = NEW[q]["items"].get(item)
            diff = r["after"] - mv
            ok = abs(diff) <= 0.5 + 1e-6 or (abs(diff) <= 1.0 + 1e-6 and r["la"])  # printed to 백만원 (half-up) -> |diff| <= 0.5; one extra unit tolerated for rounded sums
            say(f"     i{item:>2} {r['label'][:24]:24s} 조정전 {r['pb']:>10s} (L{r['lb']}) 조정후 {r['pa']:>10s} (L{r['la']}) | re-read {mv:>14,.3f} | |조정후 - re-read| = {abs(diff):.3f} -> {'OK' if abs(diff) <= 1.0 else 'FAIL'}")
            if abs(diff) > 1.0:
                problem(f"{q} i{item}", f"issuer 조정후 {r['pa']} vs re-read {mv}")
    say("")

    # ---------------------------------------------------------------- B4. CSM cells vs plan
    say("== B4. every planned CSM cell: stored value (억원, 1 decimal), exact 2-decimal value, label, line, printed")
    n_c = n_c_ok = 0
    plan_csm = {}
    CSM_MINE = {}
    for q in QUARTERS:
        rows = CSMN[q]["rows"]
        vec_exact = []
        for i in range(1, 7):
            r = rows[i]
            if r is None:
                problem(f"{q} CSM i{i}", "row not found")
                vec_exact.append(None)
                continue
            vec_exact.append(round(r["mn"] / 100.0 + 0.0, 2))
        CSM_MINE[q] = vec_exact
    for cb in PLAN["csm_buckets"]:
        q = cb["quarter"]
        T = CSMN[q]
        if not cb["file"].startswith(F[NEWKEY[q]]):
            problem(f"{q} CSM", f"plan file {cb['file']} != {F[NEWKEY[q]]}")
        if cb["file"].split("table@L")[1].split(" ")[0] != str(T["table"][0]):
            problem(f"{q} CSM", f"plan table L{cb['file']} != re-read table L{T['table'][0]}")
        for c in cb["cells"]:
            n_c += 1
            i = c["item"]
            plan_csm[(q, i)] = c
            r = T["rows"][i]
            exact = round(r["mn"] / 100.0, 2)
            stored = round(exact, 1)
            pv = c["new"] + (0.1 if MUTATE == "val" and q == "2023.3Q" and i == 6 else 0.0)
            msgs = []
            if abs(stored - pv) > 1e-9:
                msgs.append(f"stored plan {pv} != re-read {stored} (exact {exact})")
            if c.get("exact") is not None and abs(exact - c["exact"]) > 1e-9:
                msgs.append(f"exact plan {c['exact']} != {exact}")
            for p in c["parts"]:
                ln = p["line"] + (1 if MUTATE == "line" and q == "2023.1Q" and i == 1 else 0)
                if ln != r["line"] or p["printed"] != r["printed"]:
                    msgs.append(f"part L{ln} {p['printed']} != re-read L{r['line']} {r['printed']}")
                if nspace(p["label"]) != nspace(r["label"]):
                    msgs.append(f"label {p['label']!r} != {r['label']!r}")
                if p["unit"] != "백만원" and p["unit"] != T["unit"] and "억원" not in str(p["unit"]):
                    msgs.append(f"unit {p['unit']}")
                if abs(p["contribution_eok"] - exact) > 1e-9:
                    msgs.append(f"part contribution {p['contribution_eok']} != {exact}")
            if T["unit"] != "백만원" or (MUTATE == "unit" and q == "2023.1Q"):
                msgs.append(f"table unit {T['unit']}")
            if msgs:
                problem(f"{q} CSM i{i}", "; ".join(msgs))
            else:
                n_c_ok += 1
    say(f"  planned CSM cells {n_c}, fully matching the independent re-read: {n_c_ok}")
    RES["csm_cells"] = n_c
    RES["csm_cells_ok"] = n_c_ok
    # completeness of the CSM set
    for q in QUARTERS:
        for i in range(1, 7):
            if (q, i) in plan_csm:
                continue
            lv = LIVEC.get((CODE, i, q))
            stored = round(CSM_MINE[q][i - 1], 1)
            say(f"  {q} CSM i{i}: not in the plan, live {lv['값']} vs re-read {stored} -> {'equal' if abs(lv['값'] - stored) < 1e-9 else 'DIFFERENT'}")
            if abs(lv["값"] - stored) > 1e-9:
                problem(f"{q} CSM i{i}", f"not in the plan but live {lv['값']} != re-read {stored}")
    # roll-forward closure of the printed vectors and of the stored 1-decimal vectors; opening / FY boundary
    say("\n  CSM roll-forward closure (printed, 백만원) and stored (억원 1 decimal):")
    for q in QUARTERS:
        v = [CSMN[q]["rows"][i]["mn"] for i in range(1, 7)]
        res = v[0] + v[1] + v[2] + v[3] + v[4] - v[5]
        st = [round(x / 100.0, 1) for x in v]
        res_st = st[0] + st[1] + st[2] + st[3] + st[4] - st[5]
        say(f"    {q}: printed {v} closure residual {res:+.1f} 백만원 | stored {st} residual {res_st:+.2f} 억원")
        if abs(res) > 0.5:
            problem(f"{q} CSM", f"printed roll-forward does not close ({res})")
    opens = {q: CSMN[q]["rows"][1]["mn"] for q in QUARTERS}
    say(f"    FY2023 opening per quarter: {opens} -> {'ONE vintage' if len(set(opens.values())) == 1 else 'MIXED'}")
    if len(set(opens.values())) != 1:
        problem("FY2023 CSM", "openings differ within the FY")
    n1c = csm_tables(F["N1"])["cur"]["rows"][1]
    say(f"    FY boundary: 2023.4Q closing {CSMN['2023.4Q']['rows'][6]['printed']} (L{CSMN['2023.4Q']['rows'][6]['line']}) == FY2024 Q1 opening {n1c['printed']} (L{n1c['line']}) -> {'EQUAL' if CSMN['2023.4Q']['rows'][6]['mn'] == n1c['mn'] else 'BREAK'}")
    if CSMN["2023.4Q"]["rows"][6]["mn"] != n1c["mn"]:
        problem("FY boundary", "2023.4Q closing != 2024.1Q opening")

    # ---------------------------------------------------------------- C. identities
    say("\n== C. statement identities from freshly read printed cells (백만원)")
    for q in QUARTERS:
        for name, d, ok in identities(NEW[q]["vec"]):
            say(f"  {q} {name}: {d:+.6f} {'OK' if ok else 'FAIL'}")
            if not ok:
                problem(f"{q} identity", f"{name} residual {d}")
        it = NEW[q]["items"]
        # the master's bridge: item1 = item2 + item15 - item16 (life: item13 = item14 = 0), item 3+8 = 2
        br = it[2] - it[16] - it[1]
        say(f"  {q} bridge item1 = item2 - item16 (+item15=0): residual {br:+.6f}")
        if abs(br) > 5e-6:
            problem(f"{q} bridge", f"item1 vs item2-item16 residual {br}")
        c25 = it[25] - (it[26] + it[27] + it[28] + it[30] + it[32])
        say(f"  {q} 25 = 26+27+28+30+32: {c25:+.6f}")
        if abs(c25) > 5e-6:
            problem(f"{q} oci", f"item25 vs components residual {c25}")
        c18 = it[17] - it[18] - it[19]
        if abs(c18) > 5e-6:
            problem(f"{q} i17", f"17 != 18 + 19 ({c18})")

    # ---------------------------------------------------------------- second source for the annual (audit report attachment)
    say("\n== C2. second source for the annual: audit report attachment 20250331001358_00760.xml (separate FS notes)")
    try:
        Ta = csm_tables(F["N4AUD"], 0, len(lines_of(F["N4AUD"])) - 1)
        rowsA = Ta["prior"]["rows"]
        same = all(rowsA[i]["mn"] == CSMN["2023.4Q"]["rows"][i]["mn"] for i in range(1, 7))
        say(f"  CSM prior table of the attachment (L{Ta['prior']['table'][0]}): {[rowsA[i]['printed'] for i in range(1, 7)]} lines {[rowsA[i]['line'] for i in range(1, 7)]} -> {'EQUAL to the main document' if same else 'DIFFERENT'}")
        if not same:
            problem("N4AUD", "CSM prior table differs from the main document")
    except Exception as e:  # noqa
        problem("N4AUD", f"could not read the attachment CSM table: {e}")
    LA = lines_of(F["N4AUD"])
    ra, rb = 0, len(LA) - 1
    rtA = {}
    for (ta, tb) in all_tables(LA):
        rows = table_rows(LA, ta, tb)
        texts = [c["text"] for r in rows for c in r["cells"]]
        if "변경전" in texts and "변경후" in texts and any(core_label(r["cells"][0]["text"]) == "투자손익" for r in rows if r["cells"]):
            for r in rows:
                cs = r["cells"]
                if len(cs) == 3:
                    for name, item in RESTATE_MAP:
                        if core_label(cs[0]["text"]) == name:
                            rtA[item] = (mn(cs[1]["text"], "백만원"), mn(cs[2]["text"], "백만원"), cs[2]["line"])
            break
    for item, (bf, af, ln) in sorted(rtA.items()):
        mv = NEW["2023.4Q"]["items"][item]
        say(f"  attachment 재작성 table i{item}: 변경전 {bf:,.0f} 변경후 {af:,.0f} (L{ln}) | main re-read {mv:,.3f} -> {'OK' if abs(af - mv) <= 1.0 else 'FAIL'}")
        if abs(af - mv) > 1.0:
            problem("N4AUD", f"item {item} 변경후 {af} vs {mv}")
    if not rtA:
        problem("N4AUD", "attachment restatement table not found")

    # ---------------------------------------------------------------- D. seams
    say("\n== D. SEAM evidence")
    # D1: derived single quarter (difference of the restated cumulatives) vs the printed 3-month column of the same restated filing
    say("  D1 derived single quarter (cum - previous cum, both restated) vs printed 3-month column of the later filing (백만원):")
    worst = 0.0
    n_seam = 0
    for q, prevq, key in (("2023.2Q", "2023.1Q", "N2"), ("2023.3Q", "2023.2Q", "N3")):
        S = NEW[q]["S"]
        v3 = items_from(stmt_vector(S, 2023, "3m"))
        for item in sorted(v3):
            if item == 4:
                continue
            derived = NEW[q]["items"][item] - NEW[prevq]["items"][item]
            d = derived - v3[item]
            worst = max(worst, abs(d))
            n_seam += 1
            if abs(d) > 5e-6:
                problem(f"{q} i{item} seam", f"derived single quarter {derived} != printed 3-month {v3[item]} (diff {d})")
    say(f"    {n_seam} item-quarters compared, worst |derived - printed 3m| = {worst:.6f}")
    # PL4 single quarter: note (1) prints 3개월 columns in the half/third quarter reports
    for q, prevq in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
        L = lines_of(F[NEWKEY[q]])
        a, b = notes_range(L)
        n1 = NEW[q]["n1"]
        ta = n1["table"][0] - 1
        tb = n1["table"][1] - 1
        row = next(r for r in table_rows(L, ta, tb) if r["cells"] and nspace(r["cells"][0]["text"]) == "보험계약마진상각")
        nums = numeric_cells(row)
        p3m = nums[2][2]    # prior-period 3-month
        d = (NEW[q]["items"][4] - NEW[prevq]["items"][4]) - p3m
        say(f"    PL4 {q}: derived {NEW[q]['items'][4] - NEW[prevq]['items'][4]:,.0f} vs printed prior 3개월 {p3m:,.0f} (L{nums[2][1]}) diff {d:+.0f}")
        if abs(d) > 1.0:
            problem(f"{q} PL4 seam", f"derived {d}")
    # D2: FY2025 annual third column (FY2023) vs the FY2024 prior column
    say("  D2 FY2025 annual report (rcept 20260331003080) third column (제71기 = FY2023) vs the FY2024 annual prior column:")
    S25 = Stmt("A25")
    v25 = items_from(stmt_vector(S25, 2023, "cum"))
    worst25 = max(abs(v25[i] - NEW["2023.4Q"]["items"][i]) for i in v25)
    say(f"    worst |A25 - N4| over {len(v25)} items = {worst25:.6f} -> {'no later restatement of FY2023' if worst25 <= 2e-6 else 'DIFFERENT'}")
    if worst25 > 2e-6:
        problem("A25", "FY2025 annual third column differs from the FY2024 prior column")

    # ---------------------------------------------------------------- A. control (original filings vs the live pre-load master)
    say("\n== A. CONTROL: ORIGINAL FY2023 filings read with the same definitions vs the LIVE (pre-load) master")
    ctrl_bad = 0
    for q in ("2023.3Q", "2023.4Q"):
        S = Stmt(OLDKEY[q])
        vec = stmt_vector(S, 2023, "cum")
        it = items_from(vec, absolute_costs=True)
        say(f"  {q} original {S.rel} (unit {S.unit}) separate statement:")
        for item in sorted(it):
            lv = LIVE.get((CODE, item, q))
            lvv = None if lv is None else lv["값"]
            if lvv is None:
                say(f"     i{item:>2}: live master blank, original print {it[item]:,.6f}")
                continue
            d = it[item] - lvv
            tol = 2e-6 if S.unit == "원" else 0.5
            ok = abs(d) <= tol
            tag = "reproduced" if ok else "differs"
            if not ok and item == 16:
                tag = "differs (live item 16 comes from the 경영공시 PDF in 억원, original statement has no separate 기타사업비용 row)"
            say(f"     i{item:>2}: live {lvv:>16,.6f} original print {it[item]:>16,.6f} diff {d:+.6f} -> {tag}")
            if not ok and item != 16:
                ctrl_bad += 1
                problem(f"control {q} i{item}", f"definitions do not reproduce the live master ({it[item]} vs {lvv})")
        n3 = pl4_note3(OLDKEY[q], "cur")
        lv4 = LIVE[(CODE, 4, q)]["값"]
        say(f"     i 4: live {lv4:,.1f} original note (3) {n3['printed']} (L{n3['line']}) -> {'reproduced' if abs(n3['mn'] - lv4) <= 0.5 else 'differs'}")
        if abs(n3["mn"] - lv4) > 0.5:
            ctrl_bad += 1
            problem(f"control {q} i4", "original note (3) does not reproduce the live item 4")
    for q in ("2023.1Q", "2023.2Q"):
        slot = 0 if q == "2023.1Q" else 1
        sep = OldStmt(OLDKEY[q], r"^4\.\s*재무제표$")
        con = OldStmt(OLDKEY[q], r"^2\.\s*연결재무제표$")
        nm = "분기순이익" if q == "2023.1Q" else "반기순이익"
        say(f"  {q} original {sep.rel} (unit {sep.unit}): old-layout statement, separate (table L{sep.tab[0] + 1}) vs consolidated (table L{con.tab[0] + 1}) vs the live master")
        rows = [(1, "보험서비스결과"), (20, "영업이익"), (21, "영업외손익"), (22, "법인세비용차감전순이익"), (23, "법인세비용"), (24, nm)]
        for item, lab in rows:
            lv = LIVE.get((CODE, item, q))["값"]
            s_, c_ = sep.slots(lab)[slot], con.slots(lab)[slot]
            basis = []
            if abs(s_["mn"] - lv) <= 0.5:
                basis.append("separate")
            if abs(c_["mn"] - lv) <= 0.5:
                basis.append("consolidated")
            say(f"     i{item:>2} {lab:14s}: live {lv:>10,.0f} | separate {s_['printed']:>9s} (L{s_['line']}) | consolidated {c_['printed']:>9s} (L{c_['line']}) -> live equals {'/'.join(basis) if basis else 'NEITHER'}")
            if not basis:
                ctrl_bad += 1
                problem(f"control {q} i{item}", "live master equals neither the separate nor the consolidated original statement")
        d3 = (sep.slots("보험수익")[slot]["mn"] - sep.slots("보험서비스비용")[slot]["mn"])
        d8 = sep.slots("재보험손익")[slot]["mn"]
        for item, v in ((3, d3), (8, d8)):
            lv = LIVE.get((CODE, item, q))["값"]
            say(f"     i{item:>2}: live {lv:>10,.0f} | original statement lines {v:>10,.0f} -> {'reproduced' if abs(v - lv) <= 0.5 else 'differs'}")
            if abs(v - lv) > 0.5:
                ctrl_bad += 1
                problem(f"control {q} i{item}", "original lines do not reproduce the live master")
        n3 = pl4_note3(OLDKEY[q], "cur")
        lv4 = LIVE[(CODE, 4, q)]["값"]
        say(f"     i 4: live {lv4:,.1f} original note (3) {n3['printed']} (L{n3['line']}) -> {'reproduced' if abs(n3['mn'] - lv4) <= 0.5 else 'differs'}")
        if abs(n3["mn"] - lv4) > 0.5:
            ctrl_bad += 1
            problem(f"control {q} i4", "original note (3) does not reproduce the live item 4")
    # CSM control: original 'cur' tables vs the live (old) CSM values
    say("  CSM original current-period tables (separate notes) vs the live (pre-load) CSM master (억원):")
    for q in QUARTERS:
        T = csm_tables(F[OLDKEY[q]])["cur"]
        for i in range(1, 7):
            r = T["rows"][i]
            lv = LIVEC[(CODE, i, q)]["값"]
            val = None if r is None or r["mn"] is None else round(r["mn"] / 100.0, 1)
            if val is None:
                note = "printed blank (the original Q1 table leaves 보험금융비용 blank -> the master stores 0.0 there)"
                ok = (abs(lv) < 1e-9)
            else:
                ok = abs(val - lv) <= 1e-9
                note = ""
            gold_tag = "  [owner gold]" if (CODE, i, q) in GOLDC else ""
            if not ok and i == 4 and q == "2023.1Q":
                note = "live 154.8 = closing - (1+2+3+5) plug of the original Q1 (interest not printed separately)"
                ok = abs(lv - round((T["rows"][6]["mn"] - T["rows"][1]["mn"] - T["rows"][2]["mn"] - T["rows"][5]["mn"]) / 100.0, 1)) < 1e-9
            if not ok and (CODE, i, q) in GOLDC:
                note = f"owner gold {lv} (builder value `was` {GOLDC[(CODE, i, q)].get('was')}): original annual print {val}"
                ok = abs(GOLDC[(CODE, i, q)].get("was") - val) < 1e-9
            say(f"     {q} CSM i{i}: live {lv:>9,.1f} original print {('blank' if val is None else format(val, ',.1f')):>9s} -> {'reproduced' if ok else 'DIFFERS'} {note}{gold_tag}")
            if not ok:
                ctrl_bad += 1
                problem(f"control {q} CSM i{i}", "definitions do not reproduce the live CSM master")
    RES["control_bad"] = ctrl_bad

    # ---------------------------------------------------------------- E. plan sanity
    say("\n== E. plan sanity")
    contract = PLAN["apply_contract"]
    n_gn, n_gr, n_cn, n_cr = len(contract["gold_new"]), len(contract["gold_replace"]), len(contract["csm_gold_new"]), len(contract["csm_gold_replace"])
    say(f"  contract: PL gold_new {n_gn} gold_replace {n_gr} | CSM gold_new {n_cn} gold_replace {n_cr} | null_dangi_add {len(contract['null_dangi_add'])} set_dangi_add {len(contract['set_dangi_add'])} held {len(contract['held'])}")
    if n_gn + n_gr != len(plan_pl):
        problem("contract", f"PL contract {n_gn + n_gr} != planned PL cells {len(plan_pl)}")
    if n_cn + n_cr != len(plan_csm):
        problem("contract", f"CSM contract {n_cn + n_cr} != planned CSM cells {len(plan_csm)}")
    repl = {(e["quarter"], e["item"]) for e in contract["gold_replace"]}
    replc = {(e["quarter"], e["item"]) for e in contract["csm_gold_replace"]}
    if repl != APPROVED_PL_GOLD or replc != APPROVED_CSM_GOLD:
        problem("contract", f"replaced owner gold {sorted(repl)} / {sorted(replc)} != approved {sorted(APPROVED_PL_GOLD)} / {sorted(APPROVED_CSM_GOLD)}")
    # every planned cell that sits on a gold entry must be in the replace list, and vice versa
    for (q, item), c in plan_pl.items():
        on_gold = (CODE, item, q) in GOLD
        if on_gold != ((q, item) in repl):
            problem(f"{q} i{item}", f"gold overlap {on_gold} vs replace list {(q, item) in repl}")
        lv = LIVE.get((CODE, item, q))
        lvv = None if lv is None else lv["값"]
        if (lvv is None) != (c["old"] is None) or (lvv is not None and not close(lvv, c["old"], 1e-6)):
            problem(f"{q} i{item}", f"plan old {c['old']} != live master {lvv}")
    for (q, i), c in plan_csm.items():
        lv = LIVEC[(CODE, i, q)]["값"]
        if abs(lv - c["old"]) > 1e-9:
            problem(f"{q} CSM i{i}", f"plan old {c['old']} != live {lv}")
        on_gold = (CODE, i, q) in GOLDC
        if on_gold != ((q, i) in replc):
            problem(f"{q} CSM i{i}", f"gold overlap {on_gold} vs replace list")
    say(f"  old values == live master for all {len(plan_pl)} PL and {len(plan_csm)} CSM cells; replaced owner gold = {sorted(repl)} PL, {sorted(replc)} CSM (the approved list)")
    # gold class evidence
    for (q, item) in sorted(repl):
        g = GOLD[(CODE, item, q)]
        n3 = pl4_note3(OLDKEY[q], "cur")
        say(f"  PL gold {q} i{item}: gold {g['값']} == original print {n3['printed']} (L{n3['line']}) of the separate notes of rcept {Path(F[OLDKEY[q]]).stem} -> class A (original print), latest print {NEW[q]['n3']['printed']} (L{NEW[q]['n3']['line']})")
        if abs(g["값"] - n3["mn"]) > 1e-9:
            problem(f"{q} i{item}", "gold is not the original print")
    for (q, item) in sorted(replc):
        g = GOLDC[(CODE, item, q)]
        o = round(csm_tables(F[OLDKEY[q]])["cur"]["rows"][item]["mn"] / 100.0, 1)
        n = round(CSMN[q]["rows"][item]["mn"] / 100.0, 1)
        cls = "B (chain-forced: neither the original annual print nor the latest comparative)" if (abs(g["값"] - o) > 1e-9 and abs(g["값"] - n) > 1e-9) else "A"
        say(f"  CSM gold {q} i{item}: gold {g['값']} | original annual print {o} | latest comparative {n} -> class {cls}")
        if not cls.startswith("B"):
            problem(f"{q} CSM i{item}", "gold class is not B")
    ok_all = not PROBLEMS
    say(f"\nRESULT: {'ALL OK' if ok_all else str(len(PROBLEMS)) + ' PROBLEM(S)'} | PL cells {RES['pl_cells_ok']}/{RES['pl_cells']} | CSM cells {RES['csm_cells_ok']}/{RES['csm_cells']} | control problems {RES['control_bad']}")
    tag = f"_{OUTTAG}" if OUTTAG else ""
    if not MUTATE:
        # the independently re-read values (what the masters must hold after the load) for the post-load diff tool
        vals = dict(
            pl={q: {str(i): round(v, 6) for i, v in NEW[q]["items"].items()} for q in QUARTERS},
            pl_printed={q: {str(i): (NEW[q]["items"][i]) for i in NEW[q]["items"]} for q in QUARTERS},
            csm={q: [round(round(CSMN[q]["rows"][i + 1]["mn"] / 100.0, 2), 1) for i in range(6)] for q in QUARTERS},
            csm_exact={q: [round(CSMN[q]["rows"][i + 1]["mn"] / 100.0, 2) for i in range(6)] for q in QUARTERS},
            printed_3m={q: {str(i): round(v, 6) for i, v in items_from(stmt_vector(NEW[q]["S"], 2023, "3m")).items()} for q in ("2023.2Q", "2023.3Q")})
        (HERE / "kr0070_verify_values.json").write_text(json.dumps(vals, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (HERE / f"kr0070_verify{tag}.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8", newline="\n")
    (HERE / f"kr0070_verify{tag}.json").write_text(json.dumps(dict(problems=PROBLEMS, res=RES, mutate=MUTATE, ok=ok_all), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
