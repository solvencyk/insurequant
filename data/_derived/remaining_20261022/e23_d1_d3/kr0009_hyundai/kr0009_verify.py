# -*- coding: utf-8 -*-
"""KR0009 현대해상 (ticket 20261023T0900Z, D3 = FY2023 2023.1Q-2023.4Q at the latest comparative, scenario N6c_HD_FY2023_IRlegs) -- INDEPENDENT re-read of EVERY planned cell.

Own code: imports only the standard library and hd_lib.py (raw table machinery written for this verifier, no e21_* / e23_* / scripts / src module and NOT the planner), so it cannot share a defect with the
planner.  The planner output (e23_plan_hd[_final].json) is only COMPARED with what this script reads itself.

What it does
  A. CONTROL (proves the definitions): the ORIGINAL FY2023 filings (rcept 20230515002873 / 20230814003156 / 20231114002737 / 20240314001515) read with the same label definitions are compared with the LIVE
     (pre-load) master: 2023.3Q / 2023.4Q separate statement (new layout) must reproduce every Tier-1 item; 2023.1Q / 2023.2Q old layout (roman numerals) must reproduce item 4 / 5 exactly and the
     rounded 경영공시 values of items 16 / 22 / 23 / 24.
  B. CANDIDATE: FY2024 Q1 / Q2 / Q3 / annual (rcept 20240516002153 / 20240814004187 / 20241114003026 / 20250313001346), separate 4-2 statement, PRIOR-year cumulative column chosen by the dated period
     header AND the THEAD path; 보험수익 note (item 4); CSM roll-forward of the issued long-term contracts (prior table); the IR factsheet '(3) UW Income' (zipfile + XML, no openpyxl) for the LOB legs
     2 / 13 / 14 of 2023.1Q / 2023.2Q.  Compared with the plan cell by cell: value, unit, sign, row label, physical line of every part (IR: sheet cell coordinate, label cell, header cell, printed value).
  C. Identities from freshly read printed cells (statement identities, LOB legs = 보험손익, CSM roll-forward closure, PL4 == CSM item 5 from two places).
  D. SEAM evidence: derived single quarters vs the printed 3-month columns (statement, 보험수익 note, IR K column); Q4: the 9M comparative of the FY2024 Q3 report equals the live 3Q master for every
     blanked item while the annual comparative differs from the original annual print (the two cumulatives sit on different vintages).
  E. Plan sanity: old values == live master, apply-contract counts, owner-gold cells == the approved list.
Writes kr0009_verify.txt / kr0009_verify.json next to this file; exit code 1 when anything fails."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hd_lib as H  # noqa: E402
from hd_lib import ROOT, clean, nspace, parse_num, mn, close, lines_of, table_rows, all_tables, header_paths, body_rows, section, unit_above  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
_plan_default = "e23_plan_hd_final.json" if (HERE / "e23_plan_hd_final.json").exists() else "e23_plan_hd.json"
PLAN = json.loads((HERE / os.environ.get("KR0009_PLAN", _plan_default)).read_text(encoding="utf-8"))
MUTATE = os.environ.get("KR0009_MUTATE", "")      # '', 'col', 'line', 'tbl', 'val', 'unit', 'ir'
OUTTAG = os.environ.get("KR0009_OUTTAG", "")
BASE = Path(os.environ.get("KR0009_BASE", str(ROOT)))   # where the pre-load masters / gold files are read from (default: the repo root = before the load)
CODE = "KR0009"
PROBLEMS, OUT = [], []

DART = "data/dart"
F = dict(
    N1="%s/FY2024_Q1/raw/KR0009_현대해상/20240516002153.xml" % DART,
    N2="%s/FY2024_Q2/raw/KR0009_현대해상/20240814004187.xml" % DART,
    N3="%s/FY2024_Q3/raw/KR0009_현대해상/20241114003026.xml" % DART,
    N4="%s/FY2024_Q4/raw/KR0009_현대해상_20250313001346/20250313001346.xml" % DART,
    O1="%s/FY2023_Q1/raw/KR0009_현대해상/xml/20230515002873.xml" % DART,
    O2="%s/FY2023_Q2/raw/KR0009_현대해상/xml/20230814003156.xml" % DART,
    O3="%s/FY2023_Q3/raw/KR0009_현대해상/xml/20231114002737.xml" % DART,
    O4="%s/FY2023_Q4/raw/KR0009_현대해상_20240314001515/xml/20240314001515.xml" % DART,
)
IRF = {
    "2023.1Q": "data/ir/FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx",
    "2023.2Q": "data/ir/FY2024_Q2/raw/KR0009_현대해상/d33c3d385303361798f75607750ca360.xlsx",
    "2023.3Q": "data/ir/FY2024_Q3/raw/KR0009_현대해상/7a517f00b391c158b282d1412c609776.xlsx",
    "2023.4Q": "data/ir/FY2024_Q4/raw/KR0009_현대해상/2a11f147695dacd4665923059eceed11.xlsx",
}
QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
NEWKEY = {"2023.1Q": "N1", "2023.2Q": "N2", "2023.3Q": "N3", "2023.4Q": "N4"}
OLDKEY = {"2023.1Q": "O1", "2023.2Q": "O2", "2023.3Q": "O3", "2023.4Q": "O4"}
APPROVED_CSM_GOLD = {("2023.3Q", 1), ("2023.3Q", 4), ("2023.4Q", 1), ("2023.4Q", 4)}
EXPECTED_EXCLUDED = {("2023.4Q", 16)}
ITEM4_CAP = {"2023.1Q": r"^\(\d\)\s*전분기$", "2023.2Q": r"^\(\d\)\s*전반기\s*누적$", "2023.3Q": r"^\(\d\)\s*전분기\s*누적$", "2023.4Q": r"^\(\d\)\s*전기$"}
ITEM4_CAP3M = {"2023.2Q": r"^\(\d\)\s*전반기\s*3개월$", "2023.3Q": r"^\(\d\)\s*전분기\s*3개월$"}
CSM_PRIOR_CAP = {"2023.1Q": "나.전분기", "2023.2Q": "나.전반기", "2023.3Q": "나.전분기", "2023.4Q": "나.전기"}


def say(s=""):
    OUT.append(s)
    print(s)


def problem(where, msg):
    PROBLEMS.append(dict(where=where, problem=msg))
    say(f"  !! PROBLEM [{where}] {msg}")


# ------------------------------------------------------------------------------------------------ statement (separate 4-2, new layout)
LABELS = {
    "ins_result": ["보험손익"], "rev": ["보험수익"], "rerev": ["재보험수익"], "cost": ["보험서비스비용"], "recost": ["재보험서비스비용"], "other_cost": ["기타사업비용"], "inv": ["투자손익"],
    "ins_fin_rev": ["보험금융수익"], "reins_fin_rev": ["재보험금융수익"], "ins_fin_cost": ["보험금융비용"], "reins_fin_cost": ["재보험금융비용"], "op": ["영업이익(손실)"], "nonop": ["영업외손익"],
    "pretax": ["법인세차감전순이익"], "tax": ["법인세비용"], "ni": ["당기순이익(손실)"], "oci": ["기타포괄손익"], "oci_debt": ["기타포괄손익-공정가치측정채무증권평가손익"],
    "oci_credit": ["기타포괄손익-공정가치측정채무증권신용손실"], "oci_fx": ["해외사업환산손익"], "oci_hedge": ["현금흐름위험회피파생상품평가손익"], "oci_insfin": ["보험계약순금융손익"],
    "oci_reinsfin": ["재보험계약순금융손익"], "oci_equity": ["기타포괄손익-공정가치측정지분증권관련손익"], "oci_reval": ["자산재평가잉여금"], "oci_pension": ["순확정급여부채의재측정요소"], "tci": ["총포괄손익"],
}
OTHER_LEAVES = ["oci_credit", "oci_fx", "oci_reval", "oci_pension"]          # leaves that fall into item 32 (the OCI catch-all)
PERIOD_RE = re.compile(r"제\s*(\d+)\s*기\s*(?:(1분기|반기|3분기)\s*)?(\d{4})\.(\d{2})\.(\d{2})\s*부터\s*(\d{4})\.(\d{2})\.(\d{2})\s*까지")


class Stmt:
    """separate '4-2. 포괄손익계산서' of one filing: dated period list, THEAD paths, rows with ALL value cells.  Columns are chosen by the DATED period header (not by position)."""

    def __init__(self, key):
        self.key, self.rel = key, F[key]
        L = self.L = lines_of(self.rel)
        a, b = self.sec = section(L, r"^4-2\.\s*포괄손익계산서")
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
        self.unit, self.unit_line = un, unl
        self.paths = header_paths(L, ta, tb)
        self.rows = body_rows(L, ta, tb)

    def col(self, year, kind="cum"):
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

    def row(self, key, optional=False):
        want = {nspace(x) for x in LABELS[key]}
        hits = [r for r in self.rows if r["cells"] and nspace(r["cells"][0]["text"]) in want]
        if len(hits) == 0 and optional:
            return None
        if len(hits) != 1:
            raise RuntimeError(f"{self.rel}: {len(hits)} rows labelled {sorted(want)}")
        return hits[0]

    def cell(self, key, year, kind="cum"):
        j = self.col(year, kind)
        r = self.row(key)
        cs = r["cells"]
        if len(cs) != len(self.paths):
            raise RuntimeError(f"{self.rel}: row {cs[0]['text']!r} has {len(cs)} cells, header {len(self.paths)}")
        c = cs[j]
        unit = self.unit if MUTATE != "unit" else "백만원"
        v = mn(c["text"], unit)
        if v is None:
            raise RuntimeError(f"{self.rel}: {cs[0]['text']!r} col {j} not numeric {c['text']!r}")
        return dict(label=cs[0]["text"], label_line=cs[0]["line"], printed=c["text"], line=c["line"], unit=unit, mn=v, col=j, header=self.paths[j])

    def has_label(self, text):
        return any(r["cells"] and nspace(r["cells"][0]["text"]) == nspace(text) for r in self.rows)


def stmt_vector(S, year, kind="cum"):
    return {k: S.cell(k, year, kind) for k in LABELS}


def items_from(V):
    """PL Tier-1 items (백만원) by the production definitions: expenses printed in parentheses are magnitudes for 16 / 23; 19 = (보험금융수익 + 재보험금융수익) - (|보험금융비용| + |재보험금융비용|); 18 = 17 - 19;
    26 = FVOCI debt, 27 = 보험계약 순금융손익, 28 = 현금흐름위험회피, 29 = FVOCI equity, 30 = 재보험계약 순금융손익, 32 = 25 - (26..30)"""
    g = {k: V[k]["mn"] for k in V}
    it = {1: g["ins_result"], 16: abs(g["other_cost"]), 17: g["inv"], 20: g["op"], 21: g["nonop"], 22: g["pretax"], 23: abs(g["tax"]), 24: g["ni"], 25: g["oci"], 26: g["oci_debt"], 27: g["oci_insfin"],
          28: g["oci_hedge"], 29: g["oci_equity"], 30: g["oci_reinsfin"], 31: g["tci"]}
    it[19] = (g["ins_fin_rev"] + g["reins_fin_rev"]) - (abs(g["ins_fin_cost"]) + abs(g["reins_fin_cost"]))
    it[18] = it[17] - it[19]
    it[32] = it[25] - (it[26] + it[27] + it[28] + it[29] + it[30])
    return it


def identities(V, tol=2e-6):
    g = {k: V[k]["mn"] for k in V}
    out = []

    def chk(name, lhs, rhs):
        out.append((name, lhs - rhs, abs(lhs - rhs) <= tol))

    chk("보험손익 = 보험수익+재보험수익-보험서비스비용-재보험서비스비용-기타사업비용", g["ins_result"], g["rev"] + g["rerev"] - abs(g["cost"]) - abs(g["recost"]) - abs(g["other_cost"]))
    chk("영업이익 = 보험손익+투자손익", g["op"], g["ins_result"] + g["inv"])
    chk("세전이익 = 영업이익+영업외손익", g["pretax"], g["op"] + g["nonop"])
    chk("당기순이익 = 세전-법인세", g["ni"], g["pretax"] - abs(g["tax"]))
    chk("총포괄손익 = 당기순이익+기타포괄손익", g["tci"], g["ni"] + g["oci"])
    chk("기타포괄손익 = 11개 구성요소 합(26-30 + 32 의 4 잎)", g["oci"], g["oci_debt"] + g["oci_insfin"] + g["oci_hedge"] + g["oci_equity"] + g["oci_reinsfin"] + sum(g[k] for k in OTHER_LEAVES))
    return out


# ------------------------------------------------------------------------------------------------ notes
CAP_RE = re.compile(r"^\(\d\)\s*(당|전)\S*")


def notes_range(L):
    return section(L, r"^5\.\s*재무제표 주석")


def caption_above(L, ta, maxn=80):
    """nearest text line above the table (after the '(단위...)' line) that looks like '(n) 당.../전...' -> (line, text)"""
    n = 0
    for k in range(ta - 1, max(ta - 400, 0), -1):
        t = clean(L[k])
        if not t:
            continue
        n += 1
        if CAP_RE.match(t):
            return k + 1, t
        if n > maxn:
            break
    return None, None


def numeric_cells(r):
    return [(c["text"], c["line"], parse_num(c["text"])) for c in r["cells"][1:] if parse_num(c["text"]) is not None and c["text"] != ""]


_note_cache = {}


def item4_tables(key):
    """separate-notes 보험수익 tables (header 구 분 | 장기 | 자동차 | 일반 | 합계, rows 보험수익 + 보험계약마진상각): [(caption_line, caption, table, rows, unit)]"""
    if key in _note_cache:
        return _note_cache[key]
    L = lines_of(F[key])
    a, b = notes_range(L)
    out = []
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        # cheap pre-filter: the table text must mention 보험계약마진상각 and 장기 / 자동차 / 일반
        blob = " ".join(L[ta:min(tb, ta + 120)])
        if "보험계약마진상각" not in blob.replace(" ", "") or "자동차" not in blob:
            continue
        rows = table_rows(L, ta, tb)
        labs = [nspace(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if "보험계약마진상각" not in labs or "보험수익" not in labs:
            continue
        hdr = [nspace(c["text"]) for c in rows[0]["cells"]]
        if hdr != ["구분", "장기", "자동차", "일반", "합계"]:
            continue
        cl, ct = caption_above(L, ta)
        un, _ = unit_above(L, ta + 1, span=120)
        out.append((cl, ct, (ta + 1, tb + 1), rows, un))
    _note_cache[key] = out
    return out


def pl4_note(key, cap_re):
    hits = [t for t in item4_tables(key) if t[1] and re.match(cap_re, t[1])]
    if len(hits) != 1:
        raise RuntimeError(f"{F[key]}: {len(hits)} 보험수익 note tables with caption /{cap_re}/: {[(h[0], h[1]) for h in item4_tables(key)]}")
    cl, ct, tbl, rows, un = hits[0]
    unit = un if MUTATE != "unit" else "백만원"
    row = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "보험계약마진상각")       # the FIRST one is the 보험수익 section (the second one is the reinsurance-cost side)
    j = next(i for i, c in enumerate(rows[0]["cells"]) if nspace(c["text"]) == "장기")
    c = row["cells"][j]
    return dict(printed=c["text"], line=c["line"], unit=unit, mn=abs(mn(c["text"], unit)), table=tbl, caption=(cl, ct), label=row["cells"][0]["text"], label_line=row["cells"][0]["line"])


CSM_ROWS = {
    1: lambda c: c == "기초순보험계약부채",
    2: lambda c: c == "신계약효과",
    3: lambda c: c == "보험금융손익",
    4: lambda c: c == "보험계약마진을조정하는변동",
    5: lambda c: c == "보험계약마진상각",
    6: lambda c: c in ("기말보험계약순부채", "당기말보험계약순부채"),
}


def csm_prior_table(key, q):
    """CSM roll-forward of the ISSUED long-term contracts, PRIOR period: the table captioned '나. 전분기|전반기|전기' that directly follows the 장기원수 '가. 당...' table"""
    L = lines_of(F[key])
    a, b = notes_range(L)
    cand = []
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        blob = nspace(" ".join(L[ta:min(tb, ta + 140)]))
        if "보험계약마진상각" not in blob or "기초순보험계약부채" not in blob or "신계약효과" not in blob:
            continue
        cand.append((ta, tb))
    infos = []
    for (ta, tb) in cand:
        caps = []
        for k in range(ta - 1, max(ta - 120, 0), -1):
            t = clean(L[k])
            if t and not t.startswith("(단위"):
                caps.append((k + 1, t))
            if len(caps) >= 2:
                break
        infos.append(((ta, tb), caps))
    # pair: a '장기원수' + 당 table followed directly by a '나.' table
    want_prior = nspace(CSM_PRIOR_CAP[q])
    hits = []
    for idx, ((ta, tb), caps) in enumerate(infos):
        c0 = nspace(caps[0][1]) if caps else ""
        if c0 != want_prior:
            continue
        prev = infos[idx - 1] if idx > 0 else None
        prev_cap = nspace(prev[1][0][1]) if prev and prev[1] else ""
        if prev is None or "장기원수" not in prev_cap:
            continue
        hits.append((ta, tb, caps, prev))
    if len(hits) != 1:
        raise RuntimeError(f"{F[key]}: {len(hits)} prior CSM tables for {q}: {[(h[0] + 1, h[2]) for h in hits]}")
    ta, tb, caps, prev = hits[0]
    rows = table_rows(L, ta, tb)
    hdr_row = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "구분")
    jcsm = [i for i, c in enumerate(hdr_row["cells"]) if nspace(c["text"]) == "보험계약마진"]
    if len(jcsm) != 1:
        raise RuntimeError(f"{F[key]}: CSM column not unique {[c['text'] for c in hdr_row['cells']]}")
    un, _ = unit_above(L, ta + 1, span=120)
    unit = un if MUTATE != "unit" else "백만원"
    res = {}
    for item, f in CSM_ROWS.items():
        hit = [r for r in rows if r["cells"] and f(nspace(r["cells"][0]["text"]))]
        if len(hit) != 1:
            res[item] = None
            continue
        r = hit[0]
        c = r["cells"][jcsm[0]]
        res[item] = dict(label=r["cells"][0]["text"], label_line=r["cells"][0]["line"], printed=c["text"], line=c["line"], mn=mn(c["text"], unit))
    return dict(rows=res, table=(ta + 1, tb + 1), caption=caps[0], pair_cur_caption=prev[1][0], unit=unit, col=jcsm[0])


def csm_cur_table(key, q):
    """CSM roll-forward of the issued long-term contracts, CURRENT period of the same filing (the table that precedes the prior one) -- used by the 'tbl' mutation and the closing cross-check"""
    L = lines_of(F[key])
    a, b = notes_range(L)
    prior = csm_prior_table(key, q)
    infos = []
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b) or ta + 1 >= prior["table"][0]:
            continue
        blob = nspace(" ".join(L[ta:min(tb, ta + 140)]))
        if "보험계약마진상각" in blob and "기초순보험계약부채" in blob and "신계약효과" in blob:
            infos.append((ta, tb))
    ta, tb = infos[-1]
    rows = table_rows(L, ta, tb)
    hdr_row = next(r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "구분")
    jcsm = [i for i, c in enumerate(hdr_row["cells"]) if nspace(c["text"]) == "보험계약마진"][0]
    un, _ = unit_above(L, ta + 1, span=120)
    res = {}
    for item, f in CSM_ROWS.items():
        hit = [r for r in rows if r["cells"] and f(nspace(r["cells"][0]["text"]))]
        if len(hit) == 1:
            c = hit[0]["cells"][jcsm]
            res[item] = dict(label=hit[0]["cells"][0]["text"], printed=c["text"], line=c["line"], mn=mn(c["text"], un))
    return dict(rows=res, table=(ta + 1, tb + 1), unit=un)


# ------------------------------------------------------------------------------------------------ IR factsheet
def ir_legs(q):
    """'(3) UW Income' of the FY2024 IR factsheet of the LATER year: the 전년동기 누계 column (header text '<yy>.<n>Q' + newline + '누계'), the block labels in column B, the 보 험 손 익 row of each block"""
    rel = IRF[q]
    S = H.read_xlsx_sheet(rel, "(3) UW Income")
    want_hdr = f"{q[2:4]}.{q[5]}Q"
    cols = [c for c in "KLMN" if isinstance(S.get(f"{c}6"), str) and nspace(S[f"{c}6"]).startswith(want_hdr + "누계")]
    if len(cols) != 1:
        raise RuntimeError(f"{rel}: prior-year cumulative column for {want_hdr} not unique: {cols}")
    colc = cols[0] if MUTATE != "ir" else "K"
    blocks = {}                                              # block name -> row of its first line (B column)
    for r in range(7, 40):
        b = S.get(f"B{r}")
        if isinstance(b, str):
            n = nspace(b)
            if n in ("일반", "장기", "자동차"):
                blocks[n] = r
            elif n.startswith("보험손익합계"):
                blocks["합계"] = r
    order = sorted(blocks.items(), key=lambda kv: kv[1])
    res = {}
    for i, (name, r0) in enumerate(order):
        r1 = order[i + 1][1] - 1 if i + 1 < len(order) else r0 if name == "합계" else 39
        if name == "합계":
            lab_row = r0
            lab = nspace(S.get(f"B{lab_row}"))
        else:
            lab_rows = [r for r in range(r0, r1 + 1) if isinstance(S.get(f"C{r}"), str) and nspace(S[f"C{r}"]) == "보험손익"]
            if len(lab_rows) != 1:
                raise RuntimeError(f"{rel}: block {name}: {len(lab_rows)} 보험손익 rows in rows {r0}..{r1}")
            lab_row = lab_rows[0]
            lab = nspace(S[f"C{lab_row}"])
        v = S.get(f"{colc}{lab_row}")
        if not isinstance(v, float):
            raise RuntimeError(f"{rel}: {colc}{lab_row} not numeric: {v!r}")
        lab_cell = ("B" if name == "합계" else "C") + str(lab_row)
        res[name] = dict(cell=f"{colc}{lab_row}", label_cell=lab_cell, label=S.get(lab_cell), value_mn=v, block_row=r0, block_cell=f"B{r0}",
                         k_cell=f"K{lab_row}", k_value=S.get(f"K{lab_row}"))
    return dict(file=rel, sheet="(3) UW Income", col=colc, header_cell=f"{colc}6", header_text=S.get(f"{colc}6"), unit_text=S.get("L4"), cells=res, S=S)


def label_ok(label, want):
    return nspace(label) == nspace(want)


# ------------------------------------------------------------------------------------------------ old-layout statements of the ORIGINAL 2023.1Q / 2023.2Q filings (control only)
def core_label(s):
    s = nspace(re.sub(r"\(주[^)]*\)", "", s))
    return re.sub(r"^([IVXⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|\(\d+\)|\d+\)|\d+\.)", "", s)


def old_stmt(key):
    L = lines_of(F[key])
    a, b = section(L, r"^4\.\s*재무제표$")
    for (ta, tb) in all_tables(L):
        if not (a <= ta <= b):
            continue
        rows = table_rows(L, ta, tb)
        labs = [core_label(r["cells"][0]["text"]) for r in rows if r["cells"]]
        if any("법인세비용차감전순이익" == x for x in labs) and any("영업이익" == x for x in labs):
            un, _ = unit_above(L, ta + 1, span=300)
            return L, (ta, tb), rows, un
    raise RuntimeError(f"{F[key]}: old-layout income statement not found")


def old_value(rows, unit, label_core, which="cum"):
    """value cells of the old-layout statement row `label_core`: the numeric cells in order; Q1 filings [당, 전]; Q2 filings [당 3개월, 당 누적, 전 3개월, 전 누적]"""
    hits = [r for r in rows if r["cells"] and core_label(r["cells"][0]["text"]) == label_core]
    if len(hits) < 1:
        raise RuntimeError(f"old layout: no row {label_core!r}")
    r = hits[0]
    nums = [(c["text"], c["line"], mn(c["text"], unit)) for c in r["cells"][1:] if c["text"] != "" and parse_num(c["text"]) is not None]
    return nums


# ------------------------------------------------------------------------------------------------ masters
def load_masters(base):
    pl = json.loads((base / "PL_breakdown.json").read_text(encoding="utf-8"))
    cs = json.loads((base / "CSM_waterfall.json").read_text(encoding="utf-8"))
    gold = json.loads((base / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
    cgold = json.loads((base / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
    return pl, cs, gold, cgold


def r6(x):
    return None if x is None else round(x, 6)


# ------------------------------------------------------------------------------------------------ main
def main():
    pl_rows, csm_rows, gold, cgold = load_masters(BASE)
    LIVE = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_rows}
    LIVEC = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_rows}
    GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GOLDC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in cgold["set"]}
    say(f"KR0009 independent re-read | plan {PLAN.get('scenario')} | masters from {BASE} | mutation '{MUTATE}'")

    # ---------------------------------------------------------------- A. CONTROL (original filings vs LIVE master)
    say("\n== A. CONTROL: ORIGINAL FY2023 filings read with the same definitions vs the LIVE (pre-load) master")
    for q in ("2023.3Q", "2023.4Q"):
        S = Stmt(OLDKEY[q])
        vec = stmt_vector(S, 2023, "cum")
        it = items_from(vec)
        bad, notes = [], []
        for i in sorted(it):
            m = LIVE.get((CODE, i, q))
            mv = None if m is None else m["값"]
            if mv is None:
                notes.append(f"i{i}: master blank, original print {r6(it[i])}")
            elif not close(mv, it[i], 2e-6):
                notes.append(f"i{i}: master {mv} vs original print {r6(it[i])} (diff {mv - it[i]:+.6f}{', owner gold' if (CODE, i, q) in GOLD else ''})")
                if abs(mv - it[i]) > 0.05:
                    bad.append(i)
        say(f"  {q}: {S.rel} unit {S.unit} (L{S.unit_line}); {len(it)} Tier-1 items re-read; items where the LIVE master != the original print: {len(notes)}")
        for n in notes:
            say("      " + n)
        if bad:
            problem(f"A {q}", f"definitions do not reproduce the live master on items {bad}")
        for (nm, d, ok) in identities(vec):
            if not ok:
                problem(f"A {q}", f"original statement identity {nm} residual {d}")
    for q in ("2023.1Q", "2023.2Q"):
        L, tab, rows, un = old_stmt(OLDKEY[q])
        say(f"  {q}: ORIGINAL old-layout statement {F[OLDKEY[q]]} table L{tab[0] + 1}-L{tab[1] + 1} unit {un}")
        cum_idx = 0 if q == "2023.1Q" else 1                     # Q1 [당, 전]; Q2 [당 3개월, 당 누적, 전 3개월, 전 누적]
        chk = [("영업이익", 20, None), ("법인세비용차감전순이익", 22, 50.0), ("법인세비용", 23, 50.0)]
        for lab, item, tol in chk:
            try:
                nums = old_value(rows, un, lab)
            except RuntimeError as e:
                say(f"      (no old-layout row {lab}: {e})")
                continue
            m = LIVE.get((CODE, item, q))
            v = nums[cum_idx][2]
            if m is not None and m["값"] is not None and tol is not None:
                d = m["값"] - v
                say(f"      i{item} {lab}: original print {nums[cum_idx][0]} (L{nums[cum_idx][1]}) = {r6(v)} | live master {m['값']} | diff {d:+.3f} ({'within the 경영공시 억원 rounding' if abs(d) <= tol else 'OUTSIDE'})")
                if abs(d) > tol:
                    problem(f"A {q}", f"item {item}: original print {v} vs live master {m['값']}")
        try:
            v22 = old_value(rows, un, "법인세비용차감전순이익")[cum_idx][2]
            v23 = old_value(rows, un, "법인세비용")[cum_idx][2]
            m24 = LIVE[(CODE, 24, q)]["값"]
            say(f"      i24 (22 - 23 of the printed lines) = {r6(v22 - v23)} | live master {m24} | diff {m24 - (v22 - v23):+.3f} ({'within the 경영공시 억원 rounding' if abs(m24 - (v22 - v23)) <= 50.0 else 'OUTSIDE'})")
            if abs(m24 - (v22 - v23)) > 50.0:
                problem(f"A {q}", f"item 24 original {v22 - v23} vs live master {m24}")
        except RuntimeError as e:
            say(f"      (item 24 control not readable: {e})")
        try:
            n4 = old_value(rows, un, "보험계약마진상각")[cum_idx]
            m4 = LIVE[(CODE, 4, q)]["값"]
            say(f"      i4 보험계약마진상각: original print {n4[0]} (L{n4[1]}) = {r6(n4[2])} | live master {m4} -> {'EXACT' if close(n4[2], m4, 2e-3) else 'DIFFERENT'}")
            if not close(n4[2], m4, 2e-3):
                problem(f"A {q}", f"item 4 original print {n4[2]} != live master {m4}")
            n5 = old_value(rows, un, "위험조정변동")[cum_idx]
            m5 = LIVE[(CODE, 5, q)]["값"]
            say(f"      i5 위험조정변동: original print {n5[0]} (L{n5[1]}) = {r6(n5[2])} | live master {m5} -> {'EXACT' if close(n5[2], m5, 2e-3) else 'DIFFERENT'}")
        except RuntimeError as e:
            say(f"      (old-layout item 4/5 not readable: {e})")

    # ---------------------------------------------------------------- B. CANDIDATE re-read (new filings, separate statement, prior-year cumulative)
    say("\n== B. CANDIDATE: FY2024 filings, separate 4-2 statement, prior-year (2023) cumulative column, read with the production definitions")
    NEW = {}
    year = 2024 if MUTATE == "col" else 2023
    for q in QUARTERS:
        S = Stmt(NEWKEY[q])
        vec = stmt_vector(S, year, "cum")
        it = items_from(vec)
        hdr = vec["ins_result"]["header"]
        ordinal = int(re.search(r"제\s*(\d+)", hdr[0]).group(1))
        ptxt = S.periods[ordinal]["text"]
        absent15 = not S.has_label("기타영업수익")
        NEW[q] = dict(S=S, vec=vec, items=it, absent15=absent15)
        say(f"  {q}: {S.rel} | unit {S.unit} (line {S.unit_line}) | column {vec['ins_result']['col']} header {hdr} | period header (L{S.periods[ordinal]['line']}) {ptxt} | no 기타영업수익 row: {absent15}")
        for (nm, d, ok) in identities(vec):
            if not ok:
                problem(f"B {q}", f"statement identity {nm} residual {d}")
    # item 4 + CSM + IR
    for q in QUARTERS:
        try:
            n4 = pl4_note(NEWKEY[q], ITEM4_CAP[q] if MUTATE != "col" else r"^\(\d\)\s*당\S*$")
        except RuntimeError as e:
            problem(f"B {q} item 4", str(e))
            n4 = None
        NEW[q]["n4"] = n4
        if q in ITEM4_CAP3M:
            NEW[q]["n4_3m"] = pl4_note(NEWKEY[q], ITEM4_CAP3M[q])
        NEW[q]["csm"] = csm_prior_table(NEWKEY[q], q) if MUTATE != "tbl" else csm_cur_table(NEWKEY[q], q)
        if q in IRF:
            NEW[q]["ir"] = ir_legs(q)
    say("  item 4 (원수 CSM상각, 장기 열, 백만원) per quarter and the CSM roll-forward row 5 (억원) of the same filing:")
    for q in QUARTERS:
        n4, c5 = NEW[q]["n4"], NEW[q]["csm"]["rows"][5]
        if n4 is None:
            continue
        ok = abs(n4["mn"] - abs(c5["mn"])) <= 2e-3          # 1 천원 = 0.001 백만원 rounding between the two prints
        say(f"    {q}: note table L{n4['table'][0]}-{n4['table'][1]} caption {n4['caption'][1]!r} (L{n4['caption'][0]}) -> {n4['printed']} (L{n4['line']}) | CSM row 5 {c5['printed']} (L{c5['line']}) | {'AGREE (<= 0.001 mn)' if ok else 'DISAGREE'}")
        if not ok:
            problem(f"B {q} PL4", "CSM amortisation differs between the 보험수익 note and the CSM roll-forward")

    # ---------------------------------------------------------------- B1. PL cells vs plan
    say("\n== B1. every planned PL cell: value, unit, sign, row label, physical line of each part (IR: sheet cell, label cell, header cell, printed value)")
    n_cells = n_ok = 0
    plan_pl = {}
    IR_ITEM = {2: "장기", 13: "자동차", 14: "일반"}
    for b in PLAN["buckets"]:
        q = b["quarter"]
        S, vec, mine = NEW[q]["S"], NEW[q]["vec"], NEW[q]["items"]
        if b["meta"]["file"] != F[NEWKEY[q]]:
            problem(f"{q}", f"plan source file {b['meta']['file']} != {F[NEWKEY[q]]}")
        for c in b["cells"]:
            n_cells += 1
            item = c["item"]
            plan_pl[(q, item)] = c
            pv = c["new"]
            if MUTATE == "val" and q == "2023.2Q" and item == 20:
                pv += 1.0
            msgs = []
            parts_plan = c["parts"]
            if item in IR_ITEM:
                ir = NEW[q]["ir"]
                irc = ir["cells"][IR_ITEM[item]]
                mv = irc["value_mn"]
                if not close(mv, pv, 2e-6):
                    msgs.append(f"value plan {pv} != IR re-read {mv}")
                if len(parts_plan) != 1:
                    msgs.append(f"IR cell has {len(parts_plan)} plan parts")
                else:
                    p = parts_plan[0]
                    for key, want in (("cell", irc["cell"]), ("label_cell", irc["label_cell"]), ("header_cell", ir["header_cell"]), ("sheet", "(3) UW Income"), ("xlsx", ir["file"]), ("unit", "백만원")):
                        if p.get(key) != want:
                            msgs.append(f"IR part {key}: plan {p.get(key)!r} != re-read {want!r}")
                    if not label_ok(irc["label"], "보 험 손 익" if IR_ITEM[item] != "합계" else "보 험 손 익 합계"):
                        msgs.append(f"IR label cell text {irc['label']!r}")
                    if p.get("block") != IR_ITEM[item]:
                        msgs.append(f"IR block plan {p.get('block')!r} != {IR_ITEM[item]!r}")
                    if not close(float(p["printed"]), irc["value_mn"], 1e-9):
                        msgs.append(f"IR printed {p['printed']} != {irc['value_mn']!r}")
                    if not label_ok(str(ir["unit_text"]), "(단위:백만원)"):
                        msgs.append(f"IR unit text {ir['unit_text']!r}")
                    if "23." + q[5] + "Q" not in nspace(str(ir["header_text"])) or "누계" not in nspace(str(ir["header_text"])):
                        msgs.append(f"IR header text {ir['header_text']!r}")
                    if p.get("sign") != 1 or p.get("abs"):
                        msgs.append(f"IR sign/abs {p.get('sign')}/{p.get('abs')}")
                if c["unit"] != "백만원":
                    msgs.append(f"unit {c['unit']}")
            elif item == 4:
                n4 = NEW[q]["n4"]
                mv = n4["mn"]
                if not close(mv, pv, 2e-6):
                    msgs.append(f"value plan {pv} != re-read {mv}")
                if len(parts_plan) != 1:
                    msgs.append(f"{len(parts_plan)} plan parts")
                else:
                    p = parts_plan[0]
                    exp_line = n4["line"] if MUTATE != "line" else n4["line"] + 4
                    if p["line"] != exp_line:
                        msgs.append(f"line plan {p['line']} != re-read {exp_line}")
                    if p["printed"] != n4["printed"]:
                        msgs.append(f"printed plan {p['printed']!r} != {n4['printed']!r}")
                    if p["unit"] != n4["unit"]:
                        msgs.append(f"unit plan {p['unit']} != {n4['unit']}")
                    if not p.get("abs") or p.get("sign") != 1:
                        msgs.append(f"sign/abs {p.get('sign')}/{p.get('abs')} (item 4 = |CSM amortisation|)")
                    if "보험계약마진상각" not in nspace(p["label"]):
                        msgs.append(f"plan label {p['label']!r}")
            elif item == 15:
                mv = 0.0 if NEW[q]["absent15"] else None
                if mv is None or not close(mv, pv, 2e-6):
                    msgs.append(f"item 15: plan {pv}; re-read default {mv} (a 기타영업수익 row {'exists' if not NEW[q]['absent15'] else 'is absent'})")
            else:
                mv = mine.get(item)
                if mv is None or not close(mv, pv, 2e-6):
                    msgs.append(f"value plan {pv} != re-read {mv}")
                if c["unit"] != "백만원" or b["meta"]["unit"] != S.unit or (MUTATE != "unit" and S.unit != "원"):
                    msgs.append(f"unit plan {c['unit']} / meta {b['meta']['unit']} / read {S.unit}")
                # parts: every plan part (label, line, printed) must be a cell of the re-read vector (same physical line and printed text) and the signed sum must reproduce the value
                srcs = {v["line"]: (k, v) for k, v in vec.items()}
                tot = 0.0
                for p in parts_plan:
                    ln = p["line"] if MUTATE != "line" else p["line"] + 4
                    hit = srcs.get(ln)
                    if hit is None:
                        msgs.append(f"part line {ln} ({p['label']!r}) is not a re-read cell")
                        continue
                    k, v = hit
                    if p["printed"] != v["printed"]:
                        msgs.append(f"part L{ln}: printed plan {p['printed']!r} != {v['printed']!r}")
                    if nspace(p["label"]) != nspace(v["label"]):
                        msgs.append(f"part L{ln}: label plan {p['label']!r} != {v['label']!r}")
                    if p["unit"] != v["unit"]:
                        msgs.append(f"part L{ln}: unit plan {p['unit']} != {v['unit']}")
                    exp_contrib = (abs(v["mn"]) if p.get("abs") else v["mn"]) * p["sign"]
                    if not close(exp_contrib, p["contribution_mn"], 2e-6):
                        msgs.append(f"part L{ln}: contribution plan {p['contribution_mn']} != {exp_contrib}")
                    tot += exp_contrib
                if not close(tot, pv, 2e-6):
                    msgs.append(f"signed sum of the plan parts {tot} != value {pv}")
                # sign expectations: 16 and 23 are magnitudes of parenthesised costs; 19 mixes revenue(+) / cost(-) lines
                if item in (16, 23) and not (len(parts_plan) == 1 and parts_plan[0].get("abs") and parts_plan[0]["printed"].startswith("(")):
                    msgs.append(f"item {item}: expected a single parenthesised line read as a magnitude")
            if msgs:
                problem(f"B1 {q} i{item}", "; ".join(msgs))
            else:
                n_ok += 1
    say(f"  planned PL cells {n_cells}, re-read OK {n_ok}")
    if n_cells != 57:
        problem("B1", f"plan has {n_cells} PL cells (expected 57 = the 58 of the owner-approved N6c minus the rounding-only 2023.4Q item 16)")

    # B2 completeness: Tier-1 items of the statement that are NOT in the plan must equal the live master (nothing missed)
    say("\n== B2. completeness: every other Tier-1 item of the re-read vector equals the live master (or is a documented exclusion)")
    n_eq = 0
    for q in QUARTERS:
        mine = NEW[q]["items"]
        for i in sorted(mine):
            if (q, i) in plan_pl:
                continue
            m = LIVE.get((CODE, i, q))
            mv = None if m is None else m["값"]
            if mv is None:
                say(f"    {q} i{i}: master blank, re-read {r6(mine[i])} -> NOT in the plan (information)")
                problem(f"B2 {q} i{i}", "a Tier-1 item the plan does not carry is blank in the master")
            elif close(mv, mine[i], 2e-5):
                n_eq += 1
            elif (q, i) in EXPECTED_EXCLUDED:
                say(f"    {q} i{i}: EXCLUDED (rounding-only) master {mv} vs re-read {r6(mine[i])} (diff {mv - mine[i]:+.6f}); owner gold: {(CODE, i, q) in GOLD}; ledger pin exists")
            else:
                problem(f"B2 {q} i{i}", f"item differs from the master by {mine[i] - mv:+.6f} but is not in the plan")
    say(f"  Tier-1 items equal to the live master (not in the plan): {n_eq}")

    # ---------------------------------------------------------------- B3. CSM cells vs plan
    say("\n== B3. every planned CSM cell: value (억원), unit, sign, row label, physical line; CSM roll-forward closure")
    n_c = n_cok = 0
    plan_csm = {}
    for cb in PLAN["csm_buckets"]:
        q = cb["quarter"]
        T = NEW[q]["csm"]
        unit = T["unit"]
        rows = T["rows"]
        exact = {i: (rows[i]["mn"] / 100.0 if rows.get(i) else None) for i in range(1, 7)}
        if exact[4] is None:
            problem(f"B3 {q}", "CSM row 4 not found")
        vec1 = {i: round(exact[i], 1) for i in range(1, 7) if exact[i] is not None}
        resid = exact[1] + exact[2] + exact[3] + exact[4] + exact[5] - exact[6]
        say(f"  {q}: {F[NEWKEY[q]]} table L{T['table'][0]}-{T['table'][1]} caption {T['caption'][1]!r} (L{T['caption'][0]}), pair of {T['pair_cur_caption'][1]!r} | unit {unit} | exact 억원 {[round(exact[i], 5) for i in range(1, 7)]} | roll-forward residual {resid:+.5f}억")
        if abs(resid) > 2e-4:
            problem(f"B3 {q}", f"CSM roll-forward residual {resid} 억")
        if cb["file"].split(" table@L")[0] != F[NEWKEY[q]]:
            problem(f"B3 {q}", f"plan file {cb['file']}")
        for c in cb["cells"]:
            n_c += 1
            plan_csm[(q, c["item"])] = c
            item = c["item"]
            msgs = []
            pv = c["new"] if MUTATE != "val" else c["new"] + 0.1
            mv = vec1[item]
            if not close(mv, pv, 1e-9):
                msgs.append(f"value plan {pv} != re-read {mv} (exact {exact[item]})")
            if not close(c["exact"], exact[item], 2e-6):
                msgs.append(f"exact plan {c['exact']} != {exact[item]}")
            if len(c["parts"]) != 1:
                msgs.append(f"{len(c['parts'])} plan parts")
            else:
                p = c["parts"][0]
                r = rows[item]
                ln = r["line"] if MUTATE != "line" else r["line"] + 4
                if p["line"] != ln:
                    msgs.append(f"line plan {p['line']} != re-read {ln}")
                if p["printed"] != r["printed"]:
                    msgs.append(f"printed plan {p['printed']!r} != {r['printed']!r}")
                if p["unit"] != unit:
                    msgs.append(f"unit plan {p['unit']} != {unit}")
                if nspace(p["label"]) != nspace(r["label"]):
                    msgs.append(f"label plan {p['label']!r} != {r['label']!r}")
                if not close(p["contribution_eok"], exact[item], 2e-6) or p["sign"] != 1:
                    msgs.append(f"contribution {p['contribution_eok']} sign {p['sign']}")
            if msgs:
                problem(f"B3 {q} CSM i{item}", "; ".join(msgs))
            else:
                n_cok += 1
        # items NOT in the plan equal the live master (to the 1dp print rounding)
        for i in range(1, 7):
            if any(c["item"] == i for c in cb["cells"]):
                continue
            m = LIVEC.get((CODE, i, q))
            if m is None or abs(m["값"] - vec1[i]) > 0.0501:
                problem(f"B3 {q} i{i}", f"CSM item not in the plan differs from the live master: master {None if m is None else m['값']} vs re-read {vec1[i]}")
    say(f"  planned CSM cells {n_c}, re-read OK {n_cok}")
    if n_c != 18:
        problem("B3", f"plan has {n_c} CSM cells (expected 18)")
    # FY boundary / within-FY opening
    opens = [round(rows_i, 1) for rows_i in [NEW[q]["csm"]["rows"][1]["mn"] / 100.0 for q in QUARTERS]]
    say(f"  FY2023 quarterly CSM openings (latest comparative): {opens} -> {'one vintage' if max(opens) - min(opens) <= 0.05 else 'NOT one vintage'}")
    if max(opens) - min(opens) > 0.05:
        problem("B3", f"CSM openings differ within FY2023: {opens}")

    # ---------------------------------------------------------------- C. further identities
    say("\n== C. identities from freshly read cells")
    for q in ("2023.1Q", "2023.2Q"):
        ir = NEW[q]["ir"]
        legs = {k: ir["cells"][k]["value_mn"] for k in ("일반", "장기", "자동차")}
        tot = ir["cells"]["합계"]["value_mn"]
        item1 = NEW[q]["items"][1]
        s = sum(legs.values())
        say(f"  {q}: IR legs 장기 {legs['장기']!r} + 자동차 {legs['자동차']!r} + 일반 {legs['일반']!r} = {s:.6f} | IR 합계 {ir['cells']['합계']['cell']} {tot:.6f} | DART statement 보험손익 {item1:.6f} (L{NEW[q]['vec']['ins_result']['line']}) -> diff {s - item1:+.9f}")
        if not (close(s, item1, 2e-6) and close(tot, item1, 2e-6)):
            problem(f"C {q}", "IR legs do not add up to the DART separate-basis 보험손익")
        # the same IR sheet, previous-quarter columns: nothing to check; the 3-month K column is used in D
    q = "2023.4Q"
    ir4 = NEW[q]["ir"]
    sum4 = sum(ir4["cells"][k]["value_mn"] for k in ("일반", "장기", "자동차"))
    say(f"  {q} (information, NOT loaded): FY2024 Q4 IR legs 장기 {ir4['cells']['장기']['cell']}={ir4['cells']['장기']['value_mn']:.6f} 자동차 {ir4['cells']['자동차']['cell']}={ir4['cells']['자동차']['value_mn']:.6f} "
        f"일반 {ir4['cells']['일반']['cell']}={ir4['cells']['일반']['value_mn']:.6f} sum {sum4:.6f} == DART annual comparative 보험손익 {NEW[q]['items'][1]:.6f} (diff {sum4 - NEW[q]['items'][1]:+.9f}); "
        f"live master legs 2/13/14 = {LIVE[(CODE, 2, q)]['값']} / {LIVE[(CODE, 13, q)]['값']} / {LIVE[(CODE, 14, q)]['값']} (sum {LIVE[(CODE, 2, q)]['값'] + LIVE[(CODE, 13, q)]['값'] + LIVE[(CODE, 14, q)]['값']:.3f}) "
        f"-> bridge residual after the load {NEW[q]['items'][1] - (LIVE[(CODE, 2, q)]['값'] + LIVE[(CODE, 13, q)]['값'] + LIVE[(CODE, 14, q)]['값']):+.4f} mn")

    # ---------------------------------------------------------------- D. SEAMS
    say("\n== D. SEAM evidence: derived single quarters vs printed 3-month columns")
    # D1 Tier-1 items of 2023.2Q (new 2Q - new 1Q) and 2023.3Q (live/orig 3Q - new 2Q) against the 3-month column printed in the same filing
    new_cum = {q: NEW[q]["items"] for q in ("2023.1Q", "2023.2Q")}
    live_cum3 = {i: LIVE[(CODE, i, "2023.3Q")]["값"] for i in range(1, 33) if LIVE.get((CODE, i, "2023.3Q")) and LIVE[(CODE, i, "2023.3Q")]["값"] is not None}
    worst = 0.0
    n_seam = 0
    for q, prev, cur in (("2023.2Q", new_cum["2023.1Q"], new_cum["2023.2Q"]), ("2023.3Q", new_cum["2023.2Q"], live_cum3)):
        S = NEW[q]["S"]
        v3 = items_from(stmt_vector(S, 2023, "3m"))
        for i in sorted(v3):
            if i not in prev or cur.get(i) is None:
                continue
            if (q, i) not in plan_pl and not (q == "2023.3Q" and (("2023.2Q", i) in plan_pl)):
                continue
            D = cur[i] - prev[i]
            d = D - v3[i]
            worst = max(worst, abs(d))
            n_seam += 1
            if abs(d) > 3 * 2e-6:
                problem(f"D1 {q} i{i}", f"derived single quarter {D:.6f} != printed 3-month {v3[i]:.6f} (diff {d:+.6f})")
    say(f"  D1 Tier-1 single quarters (2023.2Q: 2Q-1Q; 2023.3Q: 9M-1H) vs the printed prior-year 3-month column: {n_seam} item-quarters checked, worst |diff| = {worst:.9f} mn")
    # D2 item 4: derived vs the 보험수익 note 3-month table
    for q, prev_q in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
        n43 = NEW[q]["n4_3m"]
        cur4 = NEW[q]["n4"]["mn"] if q == "2023.2Q" else LIVE[(CODE, 4, q)]["값"]
        prev4 = NEW[prev_q]["n4"]["mn"]
        D = cur4 - prev4
        say(f"  D2 item 4 {q}: derived {D:.6f} | printed 3-month (note table L{n43['table'][0]}, caption {n43['caption'][1]!r}) {n43['printed']} (L{n43['line']}) = {n43['mn']:.6f} -> diff {D - n43['mn']:+.6f}")
        if abs(D - n43["mn"]) > 3e-3:
            problem(f"D2 {q}", f"item 4 derived single {D} != printed 3-month {n43['mn']}")
    # D3 IR legs: derived vs the IR K column (3-month) of the same sheet
    for q, prev_q in (("2023.2Q", "2023.1Q"),):
        ir, irp = NEW[q]["ir"], NEW[prev_q]["ir"]
        for name in ("장기", "자동차", "일반", "합계"):
            D = ir["cells"][name]["value_mn"] - irp["cells"][name]["value_mn"]
            k = ir["cells"][name]["k_value"]
            say(f"  D3 IR {name} {q}: derived (L{ir['cells'][name]['cell'][1:]} - previous sheet) {D:.6f} | printed 3-month {ir['cells'][name]['k_cell']} {k:.6f} -> diff {D - k:+.9f}")
            if abs(D - k) > 1e-6:
                problem(f"D3 {q} {name}", f"IR derived single {D} != printed {k}")
    # item 2 at 2023.3Q: live master (builder literal) vs IR Q3 sheet 9M column; derived 3Q single from the new 2Q IR cumulative
    ir3 = NEW["2023.3Q"]["ir"]
    l2 = LIVE[(CODE, 2, "2023.3Q")]["값"]
    say(f"  D3 IR 장기 2023.3Q: live master item 2 = {l2} | IR Q3 sheet L26 (9M) = {ir3['cells']['장기']['value_mn']:.6f} (diff {l2 - ir3['cells']['장기']['value_mn']:+.6f}, print rounding of the builder literal) | "
        f"derived 3Q single from the new 2Q cumulative = {l2 - NEW['2023.2Q']['ir']['cells']['장기']['value_mn']:.6f} vs IR K26 = {ir3['cells']['장기']['k_value']:.6f}")
    if abs(l2 - ir3["cells"]["장기"]["value_mn"]) > 0.06:
        problem("D3 2023.3Q", "live item 2 of 2023.3Q is not the IR 9M value")
    # D4 Q4: 9M comparative of FY2024 Q3 == live 3Q master for the blanked items; annual comparative != original annual print
    s3 = NEW["2023.3Q"]["items"]
    o4 = items_from(stmt_vector(Stmt("O4"), 2023, "cum"))
    n4i = NEW["2023.4Q"]["items"]
    blanked = sorted(i for (q, i) in plan_pl if q == "2023.4Q" and i not in (4,))
    say(f"  D4 2023.4Q: for the {len(blanked)} adopted Tier-1 items the single quarter would be (restated annual - 9M); the 9M comparative of the FY2024 Q3 report vs the live 3Q master and the annual comparative vs the ORIGINAL annual print:")
    for i in blanked:
        m3 = LIVE[(CODE, i, "2023.3Q")]["값"]
        same9 = close(s3[i], m3, 2e-5)
        changed4 = not close(n4i[i], o4[i], 2e-5)
        say(f"      i{i}: 9M comparative {s3[i]:.6f} vs live 3Q {m3:.6f} -> {'equal' if same9 else 'DIFFERENT'} | annual comparative {n4i[i]:.6f} vs original annual {o4[i]:.6f} -> {'restated' if changed4 else 'unchanged'}")
        if not (same9 and changed4):
            problem(f"D4 i{i}", "the 'unrestated 9M / restated annual' premise of the null_dangi rule does not hold for this item")
    # item 4 premise: LOB-type item, 9M cumulative equals the master (FY2024 Q3 note table prior cumulative)
    n43c = NEW["2023.3Q"]["n4"]["mn"]
    m43 = LIVE[(CODE, 4, "2023.3Q")]["값"]
    say(f"      i4: 9M note cumulative {n43c:.6f} vs live 3Q {m43:.6f} -> {'equal' if close(n43c, m43, 2e-3) else 'DIFFERENT'} | annual comparative {NEW['2023.4Q']['n4']['mn']:.6f} vs live (original) annual {LIVE[(CODE, 4, '2023.4Q')]['값']:.6f}")
    null_cells = {(c[1], c[2]) for c in PLAN["apply_contract"]["null_dangi_add"]}
    exp_null = {("2023.4Q", i) for i in blanked} | {("2023.4Q", 4)}
    if null_cells != exp_null:
        problem("D4", f"null_dangi_add {sorted(null_cells)} != items {sorted(exp_null)}")
    say(f"  null_dangi_add in the plan: {sorted(i for (q, i) in null_cells)} (2023.4Q) -> {'matches the re-read premise' if null_cells == exp_null else 'MISMATCH'}")
    # IR print of the 4Q 3-month 보험손익 (information)
    k4 = NEW["2023.4Q"]["ir"]["cells"]["합계"]["k_value"]
    say(f"  information: the FY2024 Q4 IR sheet prints the 2023.4Q 3-month 보험손익 합계 {NEW['2023.4Q']['ir']['cells']['합계']['k_cell']} = {k4:.6f}; restated annual - 9M = {n4i[1] - s3[1]:.6f}")

    # ---------------------------------------------------------------- E. plan sanity
    say("\n== E. plan sanity")
    for (q, i), c in plan_pl.items():
        m = LIVE.get((CODE, i, q))
        mv = None if m is None else m["값"]
        if (mv is None) != (c["old"] is None) or (mv is not None and not close(mv, c["old"], 1e-9)):
            problem(f"E {q} i{i}", f"plan old {c['old']} != live master {mv}")
        if (CODE, i, q) in GOLD and BASE == ROOT:
            problem(f"E {q} i{i}", "a planned PL cell is already owner gold (the plan replaces none)")
    for (q, i), c in plan_csm.items():
        m = LIVEC.get((CODE, i, q))
        if m is None or abs(m["값"] - c["old"]) > 1e-9:
            problem(f"E {q} CSM i{i}", f"plan old {c['old']} != live master {None if m is None else m['값']}")
    say(f"  old values: {len(plan_pl)} PL + {len(plan_csm)} CSM cells == the live master")
    C = PLAN["apply_contract"]
    say(f"  contract: PL gold_new {len(C['gold_new'])} gold_replace {len(C['gold_replace'])} | CSM gold_new {len(C['csm_gold_new'])} gold_replace {len(C['csm_gold_replace'])} gold_remove {len(C.get('csm_gold_remove', []))} | "
        f"null_dangi_add {len(C['null_dangi_add'])} set_dangi_add {len(C['set_dangi_add'])} held {len(C['held'])}")
    if C["gold_replace"] or C["held"] or C["set_dangi_add"] or C["null_dangi_remove"] or C["set_dangi_remove"]:
        problem("E", "unexpected contract entries (PL gold replace / held / set_dangi / null_dangi_remove)")
    touched_csm_gold = {(e["quarter"], e["item"]) for e in C["csm_gold_replace"] + C.get("csm_gold_remove", [])}
    if touched_csm_gold != APPROVED_CSM_GOLD:
        problem("E", f"owner CSM gold touched {sorted(touched_csm_gold)} != approved {sorted(APPROVED_CSM_GOLD)}")
    for e in C["csm_gold_replace"] + C.get("csm_gold_remove", []):
        k = (CODE, e["item"], e["quarter"])
        g = GOLDC.get(k)
        if g is not None and BASE == ROOT:
            if g != e["old_entry"]:
                problem("E", f"CSM gold entry {k} differs from the entry recorded in the plan")
    # classification of the four chain-forced gold cells (evidence): original print in the ORIGINAL FY2023 Q3 / Q4 CSM tables vs the gold value vs the latest comparative
    for (q, item) in sorted(APPROVED_CSM_GOLD):
        g = GOLDC.get((CODE, item, q)) if BASE == ROOT else None
        e = next((x for x in C["csm_gold_replace"] + C.get("csm_gold_remove", []) if x["quarter"] == q and x["item"] == item), None)
        if e is None:
            continue
        gv = e["old_entry"]["값"]
        was = e["old_entry"].get("was")
        say(f"  CSM gold {q} i{item}: gold {gv} | was (builder/original print) {was} | latest comparative {e['value']} -> the gold is neither the latest comparative nor the original print (class B, chain-forced: Q1-Q3 original opening 88281.1 kept)")
        if abs(gv - e["value"]) < 0.05 or (was is not None and abs(gv - was) < 0.05):
            problem("E", f"CSM gold {q} i{item} would not be class B")
    # B2/E: the excluded rounding-only cell
    c16 = LIVE[(CODE, 16, "2023.4Q")]["값"]
    say(f"  excluded 2023.4Q item 16: live master/gold {c16} vs latest comparative {NEW['2023.4Q']['items'][16]:.6f} (printed {NEW['2023.4Q']['vec']['other_cost']['printed']} L{NEW['2023.4Q']['vec']['other_cost']['line']}) -> diff {c16 - NEW['2023.4Q']['items'][16]:+.6f} mn, rounding only")

    # ---- the independently re-read values (written for kr0009_diff_vs_backup.py)
    vals = {"pl": {}, "csm": {}, "printed_3m": {}}
    for q in QUARTERS:
        d = {}
        for (qq, i), c in plan_pl.items():
            if qq != q:
                continue
            if i in IR_ITEM:
                d[str(i)] = NEW[q]["ir"]["cells"][IR_ITEM[i]]["value_mn"]
            elif i == 4:
                d[str(i)] = NEW[q]["n4"]["mn"]
            elif i == 15:
                d[str(i)] = 0.0
            else:
                d[str(i)] = NEW[q]["items"][i]
        vals["pl"][q] = d
        rows = NEW[q]["csm"]["rows"]
        vals["csm"][q] = [round(rows[i]["mn"] / 100.0, 1) for i in range(1, 7)]
    for q in ("2023.2Q", "2023.3Q"):
        v3 = items_from(stmt_vector(NEW[q]["S"], 2023, "3m"))
        vals["printed_3m"][q] = {str(i): v for i, v in v3.items()}
        vals["printed_3m"][q]["4"] = NEW[q]["n4_3m"]["mn"]
        if q == "2023.2Q":
            for name, it in (("장기", 2), ("자동차", 13), ("일반", 14)):
                vals["printed_3m"][q][str(it)] = NEW[q]["ir"]["cells"][name]["k_value"]
    (HERE / "kr0009_verify_values.json").write_text(json.dumps(vals, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    say("\n== RESULT: " + ("ALL OK, problems 0" if not PROBLEMS else f"{len(PROBLEMS)} PROBLEM(S)"))
    tag = ("_" + OUTTAG) if OUTTAG else ""
    (HERE / f"kr0009_verify{tag}.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8", newline="\n")
    (HERE / f"kr0009_verify{tag}.json").write_text(json.dumps(dict(problems=PROBLEMS, mutate=MUTATE, pl_cells=n_cells, pl_ok=n_ok, csm_cells=n_c, csm_ok=n_cok), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return 1 if PROBLEMS else 0


if __name__ == "__main__":
    raise SystemExit(main())
