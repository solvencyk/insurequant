# -*- coding: utf-8 -*-
"""KR0003 롯데손해보험 (ticket 20261023T0900Z, D2 = 2023.4Q adopted, scenario N7_Lotte_FY2023Q4) -- INDEPENDENT re-read of EVERY planned cell.

Own code: imports only the standard library (no e21_* / e23_* / scripts / src module and NOT the planner), so it cannot share a defect with the planner.
The planner output (e23_plan_lotte.json) is only COMPARED with what this script reads itself.

What it does
  A. CONTROL (proves the definitions): the ORIGINAL FY2023 annual report (rcept 20240321001822) current-year column, read with the definitions below, must reproduce the LIVE master value of
     EVERY 2023.4Q item (Tier-1 statement items 1/16..32, LOB-note items 2..14, CSM items 1..6).
  B. CANDIDATE: the FY2024 annual report (rcept 20250320001732) prior-year column (the latest comparative of FY2023) is read with the SAME definitions, column chosen by ACONTEXT 'PFY2023' AND
     by the period header line 'prior', and compared with the plan cell by cell (value, unit, sign, row label, physical line).
  C. Statement-internal identities from freshly read printed cells; LOB note totals vs the statement; CSM roll-forward closure; second CSM source (audit report attachment _00760.xml).
  D. SEAM evidence: the FY2024 Q3 report 9-month prior-year column equals the master (unrestated) for every adopted Tier-1 item -> the 2023.4Q single quarter would mix two bases.
     FY2025 annual third column (FY2023, printed in 백만원) equals the FY2024 prior column within print rounding -> no later restatement.
  E. Plan sanity: old values == live master, no owner gold on the cells, apply contract counts, exclusion of rounding-only cells.
Writes kr0003_verify.txt / kr0003_verify.json next to this file; exit code 1 when anything fails."""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / os.environ.get("KR0003_PLAN", "e23_plan_lotte.json")).read_text(encoding="utf-8"))
MUTATE = os.environ.get("KR0003_MUTATE", "")      # '', 'col' (read the current column instead of the prior), 'line' (shift cited line), 'tbl' (take the 당기 table)
OUTTAG = os.environ.get("KR0003_OUTTAG", "")
BASE = Path(os.environ.get("KR0003_BASE", str(ROOT)))   # where the pre-load masters / gold files are read from (default: the repo root = before the load)
CODE = "KR0003"
Q = "2023.4Q"
TAG = re.compile(r"<[^>]+>")
_cache = {}
PROBLEMS = []
OUT = []
RES = {}                                                     # machine readable results

F = dict(
    A24="data/dart/FY2024_Q4/raw/KR0003_롯데손해보험_20250320001732/20250320001732.xml",
    A24AUD="data/dart/FY2024_Q4/raw/KR0003_롯데손해보험_20250320001732/20250320001732_00760.xml",
    A23="data/dart/FY2023_Q4/raw/KR0003_롯데손해보험_20240321001822/20240321001822.xml",
    A23AUD="data/dart/FY2023_Q4/raw/KR0003_롯데손해보험_20240321001822/20240321001822_00760.xml",
    Q3="data/dart/FY2024_Q3/raw/KR0003_롯데손해보험/20241114002408.xml",
    A25="data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/20260319001293.xml",
)


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
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("&nbsp;", " ").replace("&amp;", "&").replace("\u3000", " ").replace("\xa0", " ")).strip()


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


def norm_label(s):
    s = nspace(s)
    s = re.sub(r"^([\u2160-\u2169]+|\d+)\.", "", s)
    s = re.sub(r"^\(\d+\)", "", s)
    s = re.sub(r"\(주[^)]*\)", "", s)
    return s.replace("(손실)", "")


def git_json(rel):
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout
    return json.loads(out.decode("utf-8"))


def sha12(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:12]


# ------------------------------------------------------------------------------------------------ raw table machinery (independent implementation)
def parse_tr(L, i, j):
    """cells of the TR spanning physical lines i..j (0-based inclusive): [dict(tag, colspan, rowspan, text, line, ctx, acode)]  (blank cells included; line = physical line of the first text)"""
    out = []
    k = i
    while k <= j:
        m = re.match(r"\s*<(TD|TE|TH)\b([^>]*)>(.*)$", L[k], re.I)
        if m:
            attrs = m.group(2)
            cs = re.search(r'COLSPAN="(\d+)"', attrs, re.I)
            rs = re.search(r'ROWSPAN="(\d+)"', attrs, re.I)
            ctx = re.search(r'ACONTEXT="([^"]*)"', attrs, re.I)
            ac = re.search(r'ACODE="([^"]*)"', attrs, re.I)
            rest = m.group(3)
            base = dict(tag=m.group(1).upper(), colspan=int(cs.group(1)) if cs else 1, rowspan=int(rs.group(1)) if rs else 1, ctx=ctx.group(1) if ctx else "", acode=ac.group(1) if ac else "")
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
    """[(a, b)] 0-based inclusive bounds of every LEAF <TABLE>...</TABLE> (tables that contain another table are skipped: their rows would mix the inner rows in)"""
    out, stack = [], []
    for k, s in enumerate(L):
        if re.match(r"\s*<TABLE\b", s, re.I):
            if stack:
                stack[-1][1] = True                # the enclosing table has a child
            stack.append([k, False])
        elif re.match(r"\s*</TABLE", s, re.I) and stack:
            a, has_child = stack.pop()
            if not has_child:
                out.append((a, k))
    return out


def header_paths(L, a, b):
    """logical column index -> header path (texts top to bottom, rowspan repeats removed) from the THEAD of the table a..b"""
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


def caption_before(L, a, back=14):
    """text of the nearest period marker  <제79(전)기> / <제80(당)기 3분기> ...  in the `back` lines above table start a (0-based)"""
    for k in range(a - 1, max(a - back, 0), -1):
        m = re.search(r"<(제\s*\d+\s*\((당|전)\)\s*기[^>]*)>", TAG.sub(lambda mm: mm.group(0) if mm.group(0).startswith("<제") else "", L[k]).replace("&lt;", "<").replace("&gt;", ">"))
        if m:
            return m.group(1), m.group(2), k + 1
        t = clean(L[k])
        m = re.search(r"(제\s*\d+\s*\((당|전)\)\s*기[^<>]{0,8})", t)
        if m and len(t) < 40:
            return m.group(1), m.group(2), k + 1
    return None, None, None


def section_title_above(L, ln):
    for k in range(ln - 1, 0, -1):
        if L[k].startswith("<TITLE") and 'ATOC="Y"' in L[k]:
            t = clean(L[k])
            if re.match(r"^\d+(-\d+)?\.", t):
                return t, k + 1
    return "", 0


def unit_above(L, ln, span=400):
    for k in range(ln - 1, max(ln - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", TAG.sub("", L[k]))
        if m:
            return m.group(1), k + 1
    return None, None


# ------------------------------------------------------------------------------------------------ Tier-1 statement
class Stmt:
    """the separate '4-2. 포괄손익계산서' of one filing: period header lines, unit, rows with ALL value cells (blank included)"""

    def __init__(self, key):
        self.key, self.rel = key, F[key]
        L = lines_of(self.rel)
        self.L = L
        self.t0 = next(k for k, s in enumerate(L) if s.startswith("<TITLE") and re.search(r"4-2\.\s*포괄손익계산서", s))
        self.t1 = next(k for k in range(self.t0 + 1, len(L)) if L[k].startswith("<TITLE"))
        self.periods = []
        for k in range(self.t0, self.t1):
            t = clean(L[k])
            m = re.search(r"제\s*(\d+)\s*기\s*(?:([1-3]분기|반기)\s*)?(\d{4})\.(\d{2})\.(\d{2})\s*부터\s*(\d{4})\.(\d{2})\.(\d{2})\s*까지", t)
            if m and "<TE" in L[k - 1] + L[k - 2] + L[k]:
                self.periods.append(dict(line=k + 1, text=t, start=f"{m.group(3)}.{m.group(4)}.{m.group(5)}", end=f"{m.group(6)}.{m.group(7)}.{m.group(8)}"))
            elif m:
                self.periods.append(dict(line=k + 1, text=t, start=f"{m.group(3)}.{m.group(4)}.{m.group(5)}", end=f"{m.group(6)}.{m.group(7)}.{m.group(8)}"))
        un = None
        for k in range(self.t0, self.t1):
            m = re.search(r"\(\s*단위\s*[:：]\s*(백만원|천원|원)\s*\)", clean(L[k]))
            if m and "주당" not in clean(L[k]) and "기본주당" not in clean(L[k]):
                un = (m.group(1), k + 1)
                break
        self.unit = un
        thead = [clean(L[k]) for k in range(self.t0, self.t1) if re.match(r"\s*<TH\b", L[k], re.I)]
        self.thead_text = " | ".join(t for t in thead if t)
        self.rows = []
        for r in table_rows(L, self.t0, self.t1 - 1):
            cs = r["cells"]
            if len(cs) < 2:
                continue
            self.rows.append(dict(tr=r["tr"], label=cs[0]["text"], label_line=cs[0]["line"], nl=norm_label(cs[0]["text"]), vals=cs[1:]))

    def row(self, nl, nth=0, expect_count=1):
        alts = nl if isinstance(nl, (tuple, list)) else (nl,)
        c = []
        for a_ in alts:
            c = [r for r in self.rows if r["nl"] == norm_label(a_)]
            if c:
                break
        if expect_count is not None and len(c) != expect_count:
            raise RuntimeError(f"{self.key}: label {nl!r} occurs {len(c)} times (expected {expect_count}): {[x['tr'] for x in c]}")
        return c[nth]

    def cell(self, nl, col, nth=0, expect_count=1):
        r = self.row(nl, nth, expect_count)
        c = r["vals"][col]
        v = parse_num(c["text"])
        if v is None:
            raise RuntimeError(f"{self.key}: {nl!r} col {col}: not a number: {c['text']!r}")
        return v, c, r


UNIT_MN = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0}


def tier1(st, col):
    """Tier-1 items 1,16..32 from column `col` (index among the row's value cells) of the statement; returns {item: dict(val, parts)} (백만원)"""
    sc = UNIT_MN[st.unit[0]]
    out = {}

    def one(item, nl, sign=1, expect=1):
        v, c, r = st.cell(nl, col, expect_count=expect)
        return dict(item=item, label=r["label"], label_line=r["label_line"], line=c["line"], printed=c["text"], ctx=c["ctx"], acode=c["acode"], sign=sign, unit=st.unit[0], contrib=sign * v * sc)

    def item(i, parts, how):
        out[i] = dict(val=sum(p["contrib"] for p in parts), parts=parts, how=how)

    item(1, [one(1, "보험손익")], "statement line")
    item(16, [one(16, "기타사업비용")], "statement line (기타사업비용 inside 보험영업비용)")
    item(17, [one(17, "투자손익")], "statement line")
    fin = [one(19, "보험금융수익", +1), one(19, "재보험금융수익", +1), one(19, "보험금융비용", -1), one(19, "재보험금융비용", -1)]
    item(19, fin, "보험금융수익 + 재보험금융수익 - 보험금융비용 - 재보험금융비용")
    item(18, [dict(p, label=p["label"] + " (from 17)") for p in out[17]["parts"]] + [dict(p, sign=-p["sign"], contrib=-p["contrib"]) for p in fin], "17 - 19")
    item(20, [one(20, "영업이익")], "statement line")
    item(21, [one(21, "영업외손익")], "statement line")
    item(22, [one(22, "법인세비용차감전순이익")], "statement line")
    item(23, [one(23, "법인세비용")], "statement line")
    item(24, [one(24, ("당기순이익", "분기순이익", "반기순이익"))], "statement line")
    item(25, [one(25, "기타포괄손익")], "statement line")
    item(26, [one(26, "기타포괄손익-공정가치측정채무증권평가손익")], "statement line (OCI leaf 1)")
    item(27, [one(27, "보험계약자산(부채)순금융손익")], "statement line (OCI leaf 4)")
    item(28, [one(28, "위험회피목적파생상품평가손익")], "statement line (OCI leaf 3)")
    item(29, [one(29, "기타포괄손익-공정가치측정지분증권평가손익")], "statement line (OCI leaf 5)")
    item(30, [one(30, "재보험계약자산(부채)순금융손익")], "statement line (OCI leaf 6)")
    item(31, [one(31, ("총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익"))], "statement line")
    leaf = sum(out[i]["val"] for i in (26, 27, 28, 29, 30))
    out[32] = dict(val=out[25]["val"] - leaf, parts=out[25]["parts"], how="25 - (26+27+28+29+30) residual")
    # identities from printed cells
    ident = {}
    ident["20=1+17"] = out[20]["val"] - (out[1]["val"] + out[17]["val"])
    ident["22=20+21"] = out[22]["val"] - (out[20]["val"] + out[21]["val"])
    ident["24=22-23"] = out[24]["val"] - (out[22]["val"] - out[23]["val"])
    ident["31=24+25"] = out[31]["val"] - (out[24]["val"] + out[25]["val"])
    rev, _c1, _r1 = st.cell("보험영업수익", col)
    try:
        exp, _c2, _r2 = st.cell("보험영업비용", col)
    except RuntimeError:
        exp, _c2, _r2 = st.cell("보험서비스비용", col)          # the original FY2023 report names the expense block 보험서비스비용
    ident["1=보험영업수익-보험영업비용"] = out[1]["val"] - (rev - exp) * sc
    ir, _c3, _r3 = st.cell("투자영업수익", col)
    ie, _c4, _r4 = st.cell("투자영업비용", col)
    ident["17=투자영업수익-투자영업비용"] = out[17]["val"] - (ir - ie) * sc
    return out, ident


def stmt_col_check(st, col, want_period_start, want_ctx_prefix=None):
    """the chosen value column corresponds to the wanted period: period header #col (current first) and (when tagged) ACONTEXT prefix"""
    ok = True
    if col >= len(st.periods) and not (len(st.periods) == 2 and col in (2, 3)):
        problem(st.key, f"column {col} has no period header line {st.periods}")
        return False
    if len(st.periods) >= col + 1 and not (len(st.periods) == 2 and col in (2, 3)):
        p = st.periods[col]
        if p["start"] != want_period_start:
            problem(st.key, f"column {col} period header {p['text']!r} starts {p['start']} != wanted {want_period_start}")
            ok = False
    if want_ctx_prefix:
        r = st.row("보험손익")
        c = r["vals"][col]
        if not c["ctx"].startswith(want_ctx_prefix):
            problem(st.key, f"column {col} ACONTEXT {c['ctx'][:24]!r} does not start with {want_ctx_prefix}")
            ok = False
    return ok


# ------------------------------------------------------------------------------------------------ LOB note
def find_lob_table(rel, which):
    """the LOB 보험수익/보험비용 note table (header 구 분|장기|일반|자동차|합 계, contains 총 보험수익) of period `which` ('당' or '전'), inside '5. 재무제표 주석'"""
    L = lines_of(rel)
    cands = []
    for (a, b) in all_tables(L):
        rows = body_rows(L, a, b)
        labs = [norm_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if "총보험수익" not in labs or "총재보험비용" not in labs:
            continue
        hdr = [nspace(c["text"]) for r in table_rows(L, a, b) if r["tr"] - 1 < (next((k for k in range(a, b + 1) if re.match(r"\s*</THEAD", L[k], re.I)), a)) for c in r["cells"]]
        if not ("장기" in hdr and "일반" in hdr and "자동차" in hdr):
            continue
        cap, gubun, cl = caption_before(L, a)
        title, tl = section_title_above(L, a + 1)
        cands.append(dict(a=a, b=b, rows=rows, cap=cap, gubun=gubun, cap_line=cl, title=title, title_line=tl))
    sel = [c for c in cands if c["gubun"] == which and c["title"].startswith("5.")]
    if len(sel) != 1:
        raise RuntimeError(f"{rel}: LOB table of period {which}: {len(sel)} candidates ({[(c['a'] + 1, c['cap'], c['title']) for c in cands]})")
    return sel[0]


def lob_items(rel, which):
    t = find_lob_table(rel, which)
    L = lines_of(rel)
    hp = header_paths(L, t["a"], t["b"])
    m_u = re.search(r"(백만원|천원|원)", hp[0][0]) if hp and hp[0] else None
    unit, ul = (m_u.group(1), t["a"] + 1) if m_u and "단위" in hp[0][0] else unit_above(L, t["a"] + 1, span=60)
    rows = t["rows"]
    # sections: a row with no number in any value cell starts a section
    cur, secs = None, []
    for r in rows:
        cs = r["cells"]
        if not cs:
            continue
        vals = cs[1:]
        if all(parse_num(c["text"]) is None for c in vals):
            cur = norm_label(cs[0]["text"])
            continue
        secs.append(dict(sec=cur, nl=norm_label(cs[0]["text"]), label=cs[0]["text"], label_line=cs[0]["line"], vals=vals))

    def cellv(sec, nl, col, nth=0):
        c = [s for s in secs if s["sec"] == sec and s["nl"] == nl]
        if len(c) <= nth:
            raise RuntimeError(f"{rel}: LOB row {sec}/{nl} missing")
        s = c[nth]
        cell = s["vals"][col]
        v = parse_num(cell["text"])
        if v is None:
            raise RuntimeError(f"{rel}: LOB cell {sec}/{nl} col {col} not a number {cell['text']!r}")
        return v, cell, s

    def leg(sec, nl, col):
        v, cell, s = cellv(sec, nl, col)
        return dict(label=s["label"], sec=sec, line=cell["line"], printed=cell["text"], val=v)

    out = dict(table=(t["a"] + 1, t["b"] + 1), caption=t["cap"], cap_line=t["cap_line"], title=t["title"], unit=unit, unit_line=ul, items={})
    for col, name in ((0, "장기"), (1, "일반"), (2, "자동차")):
        pass
    # column 0 = 장기, 1 = 일반, 2 = 자동차, 3 = 합계 (checked against the header)
    L_ = {}
    L_["rev"] = leg("보험수익", "총보험수익", 0)
    L_["cost"] = leg("보험비용", "총보험비용", 0)
    L_["rrev"] = leg("재보험수익", "총재보험수익", 0)
    L_["rcost"] = leg("재보험비용", "총재보험비용", 0)
    L_["csm"] = leg("보험수익", "보험계약마진상각", 0)
    L_["ra"] = leg("보험수익", "위험조정변동", 0)
    L_["exp"] = leg("보험수익", "예상보험금및예상기타보험서비스비용", 0)
    L_["inc"] = leg("보험비용", "발생보험금및기타서비스비용", 0)
    L_["rcsm"] = leg("재보험비용", "보험계약마진상각", 0)
    L_["rra"] = leg("재보험비용", "위험조정변동", 0)
    L_["rexp"] = leg("재보험비용", "회수예상보험금및기타보험서비스비용", 0)
    L_["rinc"] = leg("재보험수익", "발생보험금및기타재보험수익", 0)
    it = {}
    it[3] = dict(val=L_["rev"]["val"] - L_["cost"]["val"], legs=[(L_["rev"], 1), (L_["cost"], -1)], how="총 보험수익(장기) - 총 보험비용(장기)")
    it[4] = dict(val=abs(L_["csm"]["val"]), legs=[(L_["csm"], 1)], how="|보험계약마진 상각| (보험수익 구간, 장기)")
    it[5] = dict(val=L_["ra"]["val"], legs=[(L_["ra"], 1)], how="위험조정 변동 (보험수익 구간, 장기)")
    it[6] = dict(val=L_["exp"]["val"] - L_["inc"]["val"], legs=[(L_["exp"], 1), (L_["inc"], -1)], how="예상보험금 및 예상기타보험서비스비용 - 발생보험금 및 기타서비스비용 (장기)")
    it[8] = dict(val=L_["rrev"]["val"] - L_["rcost"]["val"], legs=[(L_["rrev"], 1), (L_["rcost"], -1)], how="총 재보험수익(장기) - 총 재보험비용(장기)")
    it[9] = dict(val=-abs(L_["rcsm"]["val"]), legs=[(L_["rcsm"], -1)], how="-|보험계약마진 상각| (재보험비용 구간, 장기)")
    it[10] = dict(val=L_["rra"]["val"], legs=[(L_["rra"], 1)], how="위험조정 변동 (재보험비용 구간, 장기) as printed")
    it[11] = dict(val=L_["rinc"]["val"] - L_["rexp"]["val"], legs=[(L_["rinc"], 1), (L_["rexp"], -1)], how="발생보험금 및 기타재보험수익 - 회수예상 보험금 및 기타보험서비스비용 (장기)")
    it[2] = dict(val=it[3]["val"] + it[8]["val"], legs=it[3]["legs"] + it[8]["legs"], how="3 + 8")
    # other LOBs (items 13 = 자동차, 14 = 일반): (총보험수익 - 총보험비용) + (총재보험수익 - 총재보험비용)
    for item_no, col in ((14, 1), (13, 2)):
        a1 = leg("보험수익", "총보험수익", col)
        a2 = leg("보험비용", "총보험비용", col)
        a3 = leg("재보험수익", "총재보험수익", col)
        a4 = leg("재보험비용", "총재보험비용", col)
        it[item_no] = dict(val=a1["val"] - a2["val"] + a3["val"] - a4["val"], legs=[(a1, 1), (a2, -1), (a3, 1), (a4, -1)], how=f"(총보험수익-총보험비용)+(총재보험수익-총재보험비용) col {col}")
    # total column of 총 보험수익 for the statement cross-check
    out["rev_total"] = leg("보험수익", "총보험수익", 3)
    out["rcost_total"] = leg("재보험비용", "총재보험비용", 3)
    out["items"] = it
    out["legs"] = L_
    return out


# ------------------------------------------------------------------------------------------------ CSM roll-forward
def csm_tables(rel):
    """all CSM roll-forward tables (header has 보험계약마진(CSM) / 소 계, first body row 기초순보험계약부채) with caption + title"""
    L = lines_of(rel)
    out = []
    for (a, b) in all_tables(L):
        rows = body_rows(L, a, b)
        labs = [norm_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if not labs or labs[0] != "기초순보험계약부채":
            continue
        paths = header_paths(L, a, b)
        if not paths:
            continue
        col = next((i for i, p in enumerate(paths) if len(p) >= 2 and any("보험계약마진" in nspace(x) for x in p[:-1]) and nspace(p[-1]) == "소계"), None)
        if col is None:
            continue
        cap, gubun, cl = caption_before(L, a)
        title, tl = section_title_above(L, a + 1)
        out.append(dict(a=a, b=b, rows=rows, paths=paths, col=col, cap=cap, gubun=gubun, cap_line=cl, title=title, unit=unit_above(L, a + 1, span=60)))
    return out


def csm_vector(t, rel):
    """CSM 소계 column of one table -> items 1..6 (억원 = 백만원 / 100) with citations + closure of the printed roll-forward"""
    col = t["col"]
    rows = t["rows"]
    L = lines_of(rel)
    by = {}
    for r in rows:
        cs = r["cells"]
        if not cs:
            continue
        by.setdefault(norm_label(cs[0]["text"]), []).append(r)

    def get(nl):
        c = by.get(norm_label(nl), [])
        if len(c) != 1:
            raise RuntimeError(f"{rel}: CSM row {nl!r} occurs {len(c)} times")
        r = c[0]
        cell = r["cells"][col]            # data rows: label + 7 value cells; logical col == cell index (no colspans in body rows)
        v = parse_num(cell["text"])
        if v is None:
            raise RuntimeError(f"{rel}: CSM {nl!r} 소계 cell {cell['text']!r}")
        return dict(label=r["cells"][0]["text"], label_line=r["cells"][0]["line"], line=cell["line"], printed=cell["text"], val=v)

    g = {k: get(k) for k in ("기초순보험계약부채", "최초 인식 계약", "보험금융손익", "보험계약마진을 조정하는 추정치의 변동", "보험계약마진 상각액", "기말순보험계약부채")}
    extra = {k: get(k) for k in ("보험서비스결과", "보험금융기타포괄손익", "현금흐름")}
    vec = [g["기초순보험계약부채"]["val"] / 100, g["최초 인식 계약"]["val"] / 100, g["보험금융손익"]["val"] / 100, g["보험계약마진을 조정하는 추정치의 변동"]["val"] / 100,
           g["보험계약마진 상각액"]["val"] / 100, g["기말순보험계약부채"]["val"] / 100]
    closure = g["기초순보험계약부채"]["val"] + extra["보험서비스결과"]["val"] + g["보험금융손익"]["val"] + extra["보험금융기타포괄손익"]["val"] + extra["현금흐름"]["val"] - g["기말순보험계약부채"]["val"]
    # other CSM column consistency: sub-total = 수정소급 + 공정가치 + 이 외 in the opening and closing row
    for nl in ("기초순보험계약부채", "기말순보험계약부채"):
        r = by[norm_label(nl)][0]["cells"]
        s = sum(parse_num(r[i]["text"]) for i in (col - 3, col - 2, col - 1))
        if abs(s - parse_num(r[col]["text"])) > 0.5:
            problem(rel, f"CSM {nl}: 수정소급+공정가치+이외 {s} != 소계 {r[col]['text']}")
    return dict(vec=vec, cites=g, extra=extra, closure_mn=closure, col=col, header=t["paths"][col], caption=t["cap"], table=(t["a"] + 1, t["b"] + 1))


def stored1(x):
    return round(x, 1)



def issuer_restatement_table(rel):
    """the issuer's note '재무제표 소급재작성 - 포괄손익계산서에 미치는 영향' for 제79(전)기: {normalised label: (before, effect, after)} in 백만원 (rows with 5 cells: label, note ref, 소급 전, 재작성효과, 소급 후)"""
    L = lines_of(rel)
    found = []
    for (a, b) in all_tables(L):
        hp = header_paths(L, a, b)
        if not hp:
            continue
        flat = " ".join(nspace(x) for p_ in hp for x in p_)
        if "소급전" in flat and "재작성효과" in flat and "소급후" in flat and "제79(전)기" in flat:
            rows = body_rows(L, a, b)
            labs = [norm_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
            if "보험손익" in labs and "당기순이익" in labs:
                found.append((a, b, rows))
    if len(found) != 1:
        raise RuntimeError(f"{rel}: {len(found)} candidate restatement-effect tables for the statement of comprehensive income")
    a, b, rows = found[0]
    out = {}
    for r in rows:
        cs = r["cells"]
        if len(cs) == 5:
            vals = [parse_num(c["text"]) for c in cs[2:5]]
            if None not in vals:
                out.setdefault(norm_label(cs[0]["text"]), (vals[0], vals[1], vals[2], cs[0]["line"], cs[4]["line"]))
    return (a + 1, b + 1), out

# ================================================================================================ main
def main():
    say("== KR0003 롯데손해보험 2023.4Q  independent re-read  (ticket 20261023T0900Z, scenario N7_Lotte_FY2023Q4)")
    if MUTATE:
        say(f"!! MUTATION MODE: {MUTATE} (a negative test: the run MUST report problems)")
    for k, rel in F.items():
        say(f"  source {k}: {rel}  sha256[:12]={sha12(rel)}  lines={len(lines_of(rel))}")
    pl_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((BASE / "PL_breakdown.json").read_text(encoding="utf-8"))}
    csm_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((BASE / "CSM_waterfall.json").read_text(encoding="utf-8"))}
    pl_head = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in git_json("PL_breakdown.json") if r["원보험사코드"] == CODE}
    csm_head = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in git_json("CSM_waterfall.json") if r["원보험사코드"] == CODE}
    # KR0003 rows in the working tree must equal git HEAD (the KB life load touched KR0099 only)
    n_diff = 0
    for k, r in pl_head.items():
        if (pl_live[k]["값"], pl_live[k]["값_당분기"]) != (r["값"], r["값_당분기"]):
            n_diff += 1
    for k, r in csm_head.items():
        if (csm_live[k]["값"], csm_live[k]["값_당분기"]) != (r["값"], r["값_당분기"]):
            n_diff += 1
    say(f"  base masters ({BASE}) KR0003 PL+CSM rows differing from git HEAD: {n_diff} (must be 0: nobody touched this company before the load)")
    if n_diff:
        problem("live", f"{n_diff} KR0003 cells differ from git HEAD")
    gold = json.loads((BASE / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
    cgold = json.loads((BASE / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
    gold_pl_keys = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold["set"]}
    gold_csm_keys = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in cgold["set"]}

    # ------------------------------------------------------------------ A. CONTROL on the original FY2023 annual report
    say("")
    say("== A. CONTROL: ORIGINAL FY2023 annual report (rcept 20240321001822), current-year column (col 0) vs the LIVE master 2023.4Q")
    s23 = Stmt("A23")
    say(f"  statement unit {s23.unit}, periods {[p['text'] for p in s23.periods]}")
    stmt_col_check(s23, 0, "2023.01.01")
    t23, id23 = tier1(s23, 0)
    nbad = 0
    for i in sorted(t23):
        live = pl_live.get((CODE, i, Q), {}).get("값")
        if i == 15:
            continue
        ok = live is not None and abs(t23[i]["val"] - live) <= 5e-7 + 0
        say(f"  item {i:2d}: reread {t23[i]['val']:>18.6f}  live master {live!s:>18}  {'OK' if ok else 'DIFF'}")
        if not ok:
            nbad += 1
            problem("A.tier1", f"item {i}: original-report reread {t23[i]['val']} != live master {live}")
    say(f"  identities (original report): " + ", ".join(f"{k}={v:+.6f}" for k, v in id23.items()))
    lob23 = lob_items(F["A23"], "당")
    say(f"  LOB table (original) L{lob23['table'][0]}-{lob23['table'][1]} caption {lob23['caption']!r} title {lob23['title']!r} unit {lob23['unit']}")
    for i in (2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14):
        live = pl_live.get((CODE, i, Q), {}).get("값")
        if i in (2,):
            live2 = live
        v = lob23["items"][i]["val"]
        ok = live is not None and abs(v - live) <= 1e-9
        say(f"  item {i:2d}: reread {v:>14.1f}  live master {live!s:>14}  {'OK' if ok else 'DIFF'}   [{lob23['items'][i]['how']}]")
        if not ok:
            problem("A.lob", f"item {i}: original-report reread {v} != live master {live}")
    v7 = lob23["items"][3]["val"] - (lob23["items"][4]["val"] + lob23["items"][5]["val"] + lob23["items"][6]["val"])
    v12 = lob23["items"][8]["val"] - (lob23["items"][9]["val"] + lob23["items"][10]["val"] + lob23["items"][11]["val"])
    for i, v in ((7, v7), (12, v12)):
        live = pl_live[(CODE, i, Q)]["값"]
        say(f"  item {i:2d}: derived {v:>14.1f}  live master {live!s:>14}  {'OK' if abs(v - live) < 1e-9 else 'DIFF'}   [{'3-(4+5+6)' if i == 7 else '8-(9+10+11)'}]")
        if abs(v - live) > 1e-9:
            problem("A.lob", f"item {i}: derived {v} != live master {live}")
    # item 16 bridge sanity of the original: 2 + 13 + 14 - 16 vs 1
    bridge23 = lob23["items"][2]["val"] + lob23["items"][13]["val"] + lob23["items"][14]["val"] - t23[16]["val"] - t23[1]["val"]
    say(f"  LOB bridge (original) 2+13+14-16-1 = {bridge23:+.4f} mn")
    cts23 = [t for t in csm_tables(F["A23"]) if t["gubun"] == "당" and t["title"].startswith("5.")]
    if len(cts23) != 1:
        problem("A.csm", f"original report: {len(cts23)} current-year CSM tables in section 5")
    c23 = csm_vector(cts23[0], F["A23"])
    say(f"  CSM table (original) L{c23['table'][0]}-{c23['table'][1]} caption {c23['caption']!r} header {c23['header']} vec(억원) {c23['vec']} closure {c23['closure_mn']}")
    for i in range(1, 7):
        live = csm_live[(CODE, i, Q)]["값"]
        ok = abs(stored1(c23["vec"][i - 1]) - live) <= 0.0501
        say(f"  CSM item {i}: reread {c23['vec'][i - 1]:.2f} (stored {stored1(c23['vec'][i - 1])})  live master {live}  {'OK' if ok else 'DIFF'}")
        if not ok:
            problem("A.csm", f"item {i}: original-report reread {c23['vec'][i - 1]} vs live master {live}")
    RES["control_nbad"] = nbad

    # ------------------------------------------------------------------ B. CANDIDATE: FY2024 annual report, prior-year column
    say("")
    say("== B. CANDIDATE: FY2024 annual report (rcept 20250320001732), prior-year (FY2023) column  vs  plan e23_plan_lotte.json")
    s24 = Stmt("A24")
    col = 0 if MUTATE == "col" else 1
    say(f"  statement unit {s24.unit}, periods {[p['text'] for p in s24.periods]}, THEAD {s24.thead_text!r}")
    stmt_col_check(s24, col, "2023.01.01", "PFY2023")
    t24, id24 = tier1(s24, col)
    say("  identities (printed cells, FY2024 report prior column): " + ", ".join(f"{k}={v:+.6f}" for k, v in id24.items()))
    for k, v in id24.items():
        if abs(v) > 1e-5:
            problem("B.ident", f"statement identity {k} residual {v}")
    lobw = "당" if MUTATE == "tbl" else "전"
    lob24 = lob_items(F["A24"], lobw)
    say(f"  LOB table L{lob24['table'][0]}-{lob24['table'][1]} caption {lob24['caption']!r} (line {lob24['cap_line']}) title {lob24['title']!r} unit {lob24['unit']}")
    if lob24["unit"] != "백만원":
        problem("B.lob", f"LOB unit {lob24['unit']}")
    # statement vs note totals (the note truncates to 백만원)
    rv, _c, _r = s24.cell("보험수익", col)
    d_rev = lob24["rev_total"]["val"] - rv * 1e-6 * 1.0
    d_rc = lob24["rcost_total"]["val"] - s24.cell("재보험비용", col)[0] * 1e-6
    say(f"  note total 합계 col: 총 보험수익 {lob24['rev_total']['val']:.0f} vs statement 보험수익 {rv * 1e-6:.6f} (diff {d_rev:+.3f}); 총 재보험비용 {lob24['rcost_total']['val']:.0f} vs statement 재보험비용 (diff {d_rc:+.3f})")
    if abs(d_rev) >= 1.0 or abs(d_rc) >= 1.0:
        problem("B.lob", f"note totals do not match the statement prior column: {d_rev}, {d_rc}")
    # derived items
    it24 = lob24["items"]
    v7 = it24[3]["val"] - (it24[4]["val"] + it24[5]["val"] + it24[6]["val"])
    v12 = it24[8]["val"] - (it24[9]["val"] + it24[10]["val"] + it24[11]["val"])
    # bridge
    bridge = it24[2]["val"] + it24[13]["val"] + it24[14]["val"] - t24[16]["val"] - t24[1]["val"]
    say(f"  LOB bridge 2+13+14-16-1 = {bridge:+.4f} mn   (planner reports -0.7466)")
    # CSM
    cts = [t for t in csm_tables(F["A24"]) if t["title"].startswith("5.")]
    say(f"  CSM roll-forward tables in section 5: {[(t['a'] + 1, t['cap'], t['paths'][t['col']]) for t in cts]}")
    want = "당" if MUTATE == "tbl" else "전"
    sel = [t for t in cts if t["gubun"] == want]
    if len(sel) != 1:
        problem("B.csm", f"expected exactly one {want}-period CSM roll-forward table in section 5, found {len(sel)}")
    c24 = csm_vector(sel[0], F["A24"])
    say(f"  CSM table L{c24['table'][0]}-{c24['table'][1]} caption {c24['caption']!r} header path {c24['header']} vec(억원) {[round(x, 4) for x in c24['vec']]} printed-roll-forward closure {c24['closure_mn']:+.0f} 백만원")
    if abs(c24["closure_mn"]) > 0.5:
        problem("B.csm", f"printed CSM roll-forward does not close: {c24['closure_mn']}")
    # audit report attachment (second source in the same filing)
    cta = [t for t in csm_tables(F["A24AUD"]) if t["gubun"] == want]
    say(f"  audit-report attachment CSM tables ({want}): {[(t['a'] + 1, t['cap'], t['title'][:30]) for t in cta]}")
    if cta:
        caud = csm_vector(cta[-1] if len(cta) > 1 else cta[0], F["A24AUD"])
        say(f"  audit-report CSM vec(억원) {[round(x, 4) for x in caud['vec']]} (table L{caud['table'][0]})")
        same = all(abs(a - b) <= 1e-9 for a, b in zip(caud["vec"], c24["vec"]))
        say(f"  main report vs audit-report attachment vector identical: {same}")
        if not same:
            problem("B.csm", f"main {c24['vec']} != audit attachment {caud['vec']}")
    else:
        problem("B.csm", "no CSM table in the audit-report attachment for a cross-check")

    # ---- compare with the plan, cell by cell
    say("")
    say("  cell-by-cell comparison with the plan (new value, physical line, printed text, sign, unit)")
    bucket = next(b for b in PLAN["buckets"] if b["quarter"] == Q)
    n_ok = 0
    allnew = {}
    for i, v in t24.items():
        allnew[i] = v["val"]
    for i in (2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14):
        allnew[i] = it24[i]["val"]
    # items 7 / 12 follow the planner's rule: residual of the FINAL legs (item 6 kept at the master value when its change is rounding-only)
    live6 = pl_live[(CODE, 6, Q)]["값"]
    adopted_set = {c["item"] for c in bucket["cells"]}
    six = it24[6]["val"] if 6 in adopted_set else live6
    allnew[7] = it24[3]["val"] - (it24[4]["val"] + it24[5]["val"] + six)
    allnew[12] = it24[8]["val"] - (it24[9]["val"] + it24[10]["val"] + it24[11]["val"])
    # classification of EVERY item vs the live master
    cls = {}
    for i in sorted(allnew):
        if i == 15:
            continue
        old = pl_live.get((CODE, i, Q), {}).get("값")
        d = None if old is None else allnew[i] - old
        lobi = i in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
        if old is None:
            cls[i] = "fill"
        elif abs(d) <= 5e-7:
            cls[i] = "equal"
        elif lobi and abs(d) <= 1.0 + 1e-3:
            cls[i] = "rounding-only (LOB note prints truncated 백만원)"
        else:
            cls[i] = "changed"
    for i in sorted(cls):
        old = pl_live.get((CODE, i, Q), {}).get("값")
        say(f"  item {i:2d}: old {old!s:>16}  reread {allnew[i]:>18.6f}  delta {('-' if old is None else format(allnew[i] - old, '+.6f')):>14}  {cls[i]}")
    planned = {c["item"]: c for c in bucket["cells"]}
    for i, c in sorted(planned.items()):
        v = allnew[i]
        good = abs(v - c["new"]) <= 5e-7
        # citation check
        cite_ok = True
        if i in t24:
            parts = t24[i]["parts"]
            plp = c["parts"]
            lines_mine = sorted(p["line"] for p in parts if p["sign"] != 0)
            lines_plan = sorted(p["line"] for p in plp)
            if i == 18:
                continue
            if lines_mine != lines_plan:
                cite_ok = False
                problem("B.cite", f"item {i}: lines read {lines_mine} != plan {lines_plan}")
            for p in parts:
                pp = next((x for x in plp if x["line"] == p["line"]), None)
                if pp is not None and (pp["printed"] != p["printed"] or pp["unit"] != p["unit"] or pp["sign"] != p["sign"]):
                    cite_ok = False
                    problem("B.cite", f"item {i} line {p['line']}: printed/unit/sign {p['printed']!r}/{p['unit']}/{p['sign']} != plan {pp['printed']!r}/{pp['unit']}/{pp['sign']}")
        elif i in lob24["items"]:
            legs = lob24["items"][i]["legs"]
            lines_mine = sorted(l["line"] for l, _s in legs)
            lines_plan = sorted(p["line"] for p in c["parts"])
            if i in (7, 12):
                pass
            elif lines_mine != lines_plan:
                cite_ok = False
                problem("B.cite", f"item {i}: lines read {lines_mine} != plan {lines_plan}")
        ok = good and cite_ok and cls.get(i) in ("changed", "fill")
        if not good:
            problem("B.value", f"item {i}: independent reread {v} != plan new {c['new']}")
        if cls.get(i) not in ("changed", "fill"):
            problem("B.class", f"item {i}: planned but classified {cls.get(i)}")
        if abs(c["old"] - pl_live[(CODE, i, Q)]["값"]) > 5e-7:
            problem("B.old", f"item {i}: plan old {c['old']} != live master {pl_live[(CODE, i, Q)]['값']}")
        if (CODE, i, Q) in gold_pl_keys:
            problem("B.gold", f"item {i} already has an owner-gold entry (not expected)")
        n_ok += 1 if ok else 0
    say(f"  PL cells planned {len(planned)}; independently confirmed {n_ok}")
    RES["pl_confirmed"] = n_ok
    RES["pl_planned"] = sorted(planned)
    dropped_plan = {d["item"]: d for d in bucket["dropped"]}
    for i, d in dropped_plan.items():
        say(f"  plan dropped item {i}: old {d['old']} new {d['new']} ({d['cls']}); my classification: {cls.get(i)}")
        if not cls.get(i, "").startswith("rounding"):
            problem("B.drop", f"plan dropped item {i} but my classification is {cls.get(i)}")
    # every item classified changed/fill must be in the plan
    for i, c_ in cls.items():
        if c_ in ("changed", "fill") and i not in planned:
            problem("B.missing", f"item {i} classified {c_} by the independent read but not planned")
    # CSM comparison
    cb = next(x for x in PLAN["csm_buckets"] if x["quarter"] == Q)
    csm_planned = {c["item"]: c for c in cb["cells"]}
    n_csm = 0
    for i in range(1, 7):
        exact = c24["vec"][i - 1]
        sv = stored1(exact)
        old = csm_live[(CODE, i, Q)]["값"]
        ch = abs(sv - old) > 0.0501
        pc = csm_planned.get(i)
        cite = c24["cites"][["기초순보험계약부채", "최초 인식 계약", "보험금융손익", "보험계약마진을 조정하는 추정치의 변동", "보험계약마진 상각액", "기말순보험계약부채"][i - 1]]
        say(f"  CSM item {i}: old {old}  exact {exact:.2f} stored {sv}  line {cite['line']} printed {cite['printed']} ({cite['label']!r})  planned {'new=' + str(pc['new']) if pc else '-'}  {'changed' if ch else 'equal(rounding)'}")
        if ch != (pc is not None):
            problem("B.csm", f"item {i}: changed={ch} but planned={pc is not None}")
        if pc is not None:
            if abs(pc["new"] - sv) > 1e-9 or abs(pc["exact"] - exact) > 1e-6 or pc["parts"][0]["line"] != cite["line"] or pc["parts"][0]["printed"] != cite["printed"]:
                problem("B.csm", f"item {i}: plan {pc['new']}/{pc['exact']}/L{pc['parts'][0]['line']}/{pc['parts'][0]['printed']} != reread {sv}/{exact}/L{cite['line']}/{cite['printed']}")
            elif abs(old - pc["old"]) > 1e-9:
                problem("B.csm", f"item {i}: plan old {pc['old']} != live {old}")
            elif (CODE, i, Q) in gold_csm_keys:
                problem("B.gold", f"CSM item {i} already has gold")
            else:
                n_csm += 1
        if abs(exact * 100 - round(exact * 100)) > 1e-6:
            problem("B.csm", f"item {i}: not an integer 백만원 {exact * 100}")
    say(f"  CSM cells planned {len(csm_planned)}; independently confirmed {n_csm}")
    RES["csm_confirmed"] = n_csm
    ex = c24["vec"]
    say(f"  PL4 vs CSM5 pair: item 4 {allnew[4]:.0f} 백만원 vs |CSM 상각| {abs(ex[4]) * 100:.0f} 백만원 -> diff {allnew[4] - abs(ex[4]) * 100:+.3f}")
    if abs(allnew[4] - abs(ex[4]) * 100) > 0.5:
        problem("B.pair", "PL4 and CSM5 differ")
    stored = [stored1(x) for x in ex]
    say(f"  stored CSM vector {stored}; 1-dp closure residual {stored[0] + stored[1] + stored[2] + stored[3] + stored[4] - stored[5]:+.2f}; tie note: -1859.05 -> round() -> {stored1(-1859.05)} (python float rounding, the repo convention)")

    # ------------------------------------------------------------------ C. merged vector identities
    say("")
    say("== C. merged vector identities (live master for the unchanged items + reread for the changed ones)")
    merged = {i: (allnew[i] if i in planned else pl_live[(CODE, i, Q)]["값"]) for i in range(1, 33) if (CODE, i, Q) in pl_live}
    mid = {
        "20-(1+17)": merged[20] - (merged[1] + merged[17]),
        "22-(20+21)": merged[22] - (merged[20] + merged[21]),
        "24-(22-23)": merged[24] - (merged[22] - merged[23]),
        "31-(24+25)": merged[31] - (merged[24] + merged[25]),
        "25-(26+27+28+29+30+32)": merged[25] - sum(merged[i] for i in (26, 27, 28, 29, 30, 32)),
        "17-(18+19)": merged[17] - (merged[18] + merged[19]),
        "3-(4+5+6+7)": merged[3] - (merged[4] + merged[5] + merged[6] + merged[7]),
        "8-(9+10+11+12)": merged[8] - (merged[9] + merged[10] + merged[11] + merged[12]),
        "2-(3+8)": merged[2] - (merged[3] + merged[8]),
        "1-(2+13+14+15-16)": merged[1] - (merged[2] + merged[13] + merged[14] + merged[15] - merged[16]),
    }
    for k, v in mid.items():
        lim = 1.0 if k.startswith("1-") else 5e-6
        say(f"  {k:28s} {v:+.6f}  {'OK' if abs(v) <= lim else 'FAIL'}")
        if abs(v) > lim:
            problem("C.ident", f"{k} = {v}")
    RES["identities"] = mid

    # ------------------------------------------------------------------ D. seam evidence
    say("")
    say("== D. SEAM evidence for the 2023.4Q single quarter (값_당분기 = 4Q cumulative - 3Q cumulative)")
    sq = Stmt("Q3")
    say(f"  FY2024 Q3 report statement: unit {sq.unit}, periods {[p['text'] for p in sq.periods]}")
    tq3, idq3 = tier1(sq, 3)                       # [cur 3m, cur 9M cum, prior 3m, prior 9M cum]
    tq3_3m, _ = tier1(sq, 2)
    seam_items = sorted(planned)
    n_eq = 0
    for i in (1, 17, 19, 20, 22, 23, 24, 25, 26, 27, 31):
        live3 = pl_live[(CODE, i, "2023.3Q")]["값"]
        eq = abs(tq3[i]["val"] - live3) <= 5e-7
        n_eq += 1 if eq else 0
        say(f"  item {i:2d}: 2023.3Q master {live3:>18.6f}  FY2024 Q3 report prior 9M column {tq3[i]['val']:>18.6f}  {'EQUAL (unrestated 9M)' if eq else 'DIFFERENT'}   | derived single quarter after load = {allnew[i] - live3:+.6f} (annual new - 9M master); printed prior 3M col = n/a for Q4")
    say(f"  -> {n_eq}/11 Tier-1 9M comparatives equal the master (so the 4Q cumulative adopted from the annual comparative sits on another basis than the 9M cumulative)")
    RES["seam_equal_items"] = n_eq
    if n_eq != 11:
        problem("D.seam", f"only {n_eq}/11 Tier-1 9M comparatives equal the master (the planner proposed null_dangi for these)")
    # the FY2024 annual current column is NOT the same basis as Q3 either: the FY2023 annual comparative differs from the original (restated) -> the annual restatement does not appear in 9M
    cts3 = [t for t in csm_tables(F["Q3"]) if t["gubun"] == "전" and t["title"].startswith("5.")]
    for t in cts3:
        v3 = csm_vector(t, F["Q3"])
        say(f"  FY2024 Q3 report CSM prior-9M table L{v3['table'][0]} caption {v3['caption']!r}: vec {v3['vec']} vs master 2023.3Q {[csm_live[(CODE, i, '2023.3Q')]['값'] for i in range(1, 7)]}")
        ok3 = all(abs(stored1(a) - csm_live[(CODE, i, '2023.3Q')]['값']) <= 0.0501 for i, a in enumerate(v3["vec"], 1))
        say(f"  -> 9M CSM comparative equals the master 2023.3Q vector: {ok3}")
        if not ok3:
            problem("D.seam", "FY2024 Q3 CSM prior-9M vector differs from the master 2023.3Q")
    # FY2025 annual third column (FY2023)
    s25 = Stmt("A25")
    t25, _id25 = tier1(s25, 2)
    say(f"  FY2025 annual statement unit {s25.unit}, periods {[p['text'] for p in s25.periods]}; third column = FY2023 (백만원, printed rounded):")
    sc_ok = True
    for i in (1, 17, 19, 20, 22, 23, 24, 25, 26, 27, 31):
        d = t25[i]["val"] - allnew[i]
        ok = abs(d) <= 1.0 + 1e-6
        sc_ok &= ok
        say(f"    item {i:2d}: FY2025 report FY2023 col {t25[i]['val']:>12.1f}  vs FY2024-report prior col {allnew[i]:>16.6f}  diff {d:+.4f} {'OK' if ok else 'DIFF'}")
        if not ok:
            problem("D.fy25", f"item {i}: FY2025 annual FY2023 column {t25[i]['val']} vs FY2024 prior {allnew[i]}")
    RES["fy25_third_col_equal"] = sc_ok


    # ------------------------------------------------------------------ F. the issuer's own restatement table (note 47)
    say("")
    say("== F. issuer's OWN restatement table (FY2024 annual report, note 47 'effect on the statement of comprehensive income', 제79(전)기: 소급 전 / 재작성효과 / 소급 후, 백만원)")
    (ta, tb), rt = issuer_restatement_table(F["A24"])
    say(f"  table L{ta}-{tb}; {len(rt)} rows with 3 numbers")
    pairs = [("보험손익", 1), ("투자손익", 17), ("영업이익", 20), ("법인세비용차감전순이익", 22), ("법인세비용", 23), ("당기순이익", 24), ("기타포괄손익", 25),
             ("기타포괄손익-공정가치측정채무증권평가손익", 26), ("보험계약자산(부채)순금융손익", 27), ("총포괄손익", 31)]
    nF = 0
    for lab, it_ in pairs:
        bef, eff, aft, ll, la = rt[norm_label(lab)]
        old = pl_live[(CODE, it_, Q)]["값"]
        new_mn = allnew[it_]
        ok_after = abs(aft - new_mn) <= 1.0
        ok_before = abs(bef - old) <= 2.0
        ok_eff = abs((aft - bef) - eff) <= 1.0
        ok_delta = abs(eff - (new_mn - old)) <= 2.0
        nF += 1 if (ok_after and ok_before and ok_eff and ok_delta) else 0
        say(f"  item {it_:2d} {lab[:22]:22s}: issuer 소급전 {bef:>10,.0f} | 효과 {eff:>+9,.0f} | 소급후 {aft:>10,.0f}   ||   master old {old:>14,.3f} -> reread {new_mn:>14,.3f} (delta {new_mn - old:+,.3f})  after-ok {ok_after} before-ok {ok_before} effect-ok {ok_eff} delta-ok {ok_delta}  [L{la}]")
        if not (ok_after and ok_before and ok_eff and ok_delta):
            problem("F.issuer", f"item {it_}: issuer restatement table {bef}/{eff}/{aft} vs master old {old} / reread {new_mn}")
    fin_after = sum(rt[norm_label(x)][2] * sg for x, sg in (("보험금융수익", 1), ("재보험금융수익", 1), ("보험금융비용", -1), ("재보험금융비용", -1)))
    fin_before = sum(rt[norm_label(x)][0] * sg for x, sg in (("보험금융수익", 1), ("재보험금융수익", 1), ("보험금융비용", -1), ("재보험금융비용", -1)))
    say(f"  item 19 (보험금융수익+재보험금융수익-보험금융비용-재보험금융비용): issuer 소급전 {fin_before:,.0f} -> 소급후 {fin_after:,.0f}; master old {pl_live[(CODE, 19, Q)]['값']:,.3f} -> reread {allnew[19]:,.3f}")
    if abs(fin_after - allnew[19]) > 2.0 or abs(fin_before - pl_live[(CODE, 19, Q)]["값"]) > 3.0:
        problem("F.issuer", f"item 19: issuer table {fin_before}/{fin_after} vs master/reread")
    say(f"  -> {nF}/{len(pairs)} Tier-1 items agree with the issuer's own 소급 전 / 소급 후 table (소급 전 = the old master value, 소급 후 = the value adopted here)")
    RES["issuer_restatement_agree"] = nF

    # ------------------------------------------------------------------ E. plan sanity
    say("")
    say("== E. plan / apply-contract sanity")
    C = PLAN["apply_contract"]
    say(f"  apply contract: PL gold_new {len(C['gold_new'])}, gold_replace {len(C['gold_replace'])}; CSM gold_new {len(C['csm_gold_new'])}, gold_replace {len(C['csm_gold_replace'])}; "
        f"null_dangi_add {len(C['null_dangi_add'])}, null_dangi_remove {len(C['null_dangi_remove'])}, set_dangi_add {len(C['set_dangi_add'])}, held {C['held']}")
    if C["gold_replace"] or C["csm_gold_replace"]:
        problem("E", "the plan replaces owner gold cells; none is expected for 2023.4Q")
    if len(C["gold_new"]) != 18 or len(C["csm_gold_new"]) != 5:
        problem("E", f"expected 18 PL + 5 CSM new gold cells, got {len(C['gold_new'])} + {len(C['csm_gold_new'])}")
    nd_items = sorted(c[2] for c in C["null_dangi_add"])
    say(f"  null_dangi_add items: {nd_items}")
    RES["null_dangi_items"] = nd_items
    live_dangi = {i: pl_live[(CODE, i, Q)].get("값_당분기") for i in range(1, 33)}
    # every item with a single quarter that would be derived from a changed cumulative and an unchanged 9M must be in null_dangi; items whose 9M is blank stay blank
    for i in sorted(planned):
        q3 = pl_live.get((CODE, i, "2023.3Q"), {}).get("값")
        will_derive = q3 is not None
        nd = i in nd_items
        say(f"  item {i:2d}: 3Q cumulative {q3!s:>16} -> single quarter derivable: {will_derive}; planned null_dangi: {nd}; live 당분기 {live_dangi[i]!s}")
        if will_derive != nd:
            problem("E.seam", f"item {i}: derivable={will_derive} but null_dangi={nd}")

    RES["problems"] = PROBLEMS
    say("")
    say(f"RESULT: PL cells confirmed {RES['pl_confirmed']}/{len(RES['pl_planned'])}; CSM cells confirmed {RES['csm_confirmed']}/{len(csm_planned)}; control mismatches {RES['control_nbad']}; problems {len(PROBLEMS)}")
    suffix = ("_" + OUTTAG) if OUTTAG else ""
    (HERE / f"kr0003_verify{suffix}.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8", newline="\n")
    (HERE / f"kr0003_verify{suffix}.json").write_text(json.dumps(RES, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
    return 1 if PROBLEMS else 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as e:                                      # noqa: BLE001
        import traceback
        traceback.print_exc()
        rc = 2
    sys.exit(rc)
