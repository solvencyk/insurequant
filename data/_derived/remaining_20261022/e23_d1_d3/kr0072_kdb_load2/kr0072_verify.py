# -*- coding: utf-8 -*-
"""KR0072 케이디비생명보험 (ticket 20261023T0900Z, D3 = FY2023 2023.1Q-2023.4Q at the latest comparative, scenario N5_KDB_FY2023) -- INDEPENDENT re-read of EVERY planned cell.

Own code: imports only the standard library and the sibling helper modules kdb_raw / kdb_stmt / kdb_notes (written for this check, stdlib only; no e21_* / e23_* / scripts / src module and NOT the
planner), so it cannot share a defect with the planner.  The planner output (e23_plan_kdb*.json) is only COMPARED with what this script reads itself.

  A. CONTROL (proves the definitions): the ORIGINAL FY2023 filings (rcept 20230515002450 / 20230814003052 / 20231114002983 / 20240401002710) are read with the same label definitions and compared
     with the LIVE (pre-load) master.  2023.3Q / 2023.4Q: new layout.  2023.1Q / 2023.2Q: old (roman numeral) layout; the 2023.2Q block is the explicit RECHECK asked for by the owner round
     (cumulative vs 3-month column, the items held back as ambiguous in the builder override: 15 / 17 / 18).
  B. CANDIDATE: the FY2024 filings (rcept 20240516000597 / 20240814000801 / 20241114000809 / 20250331002302), separate 4-2 statement, PRIOR-year cumulative column chosen by the dated period header AND
     by the THEAD path, compared with the plan cell by cell (value, unit, sign, row label, physical line of every part).  CSM: separate-notes roll-forward 'prior' table, CSM column, rows by label.
  C. Statement-internal identities from freshly read printed cells; OCI block sums; CSM roll-forward closure; PL4 (CSM amortisation) from two places (구성내역 note, CSM roll-forward) must agree;
     second CSM source for the annual (audit report attachment _00760.xml).
  D. SEAM evidence: derived single quarters (cumulative differences) against the printed 3-month columns of the same filings; FY2025 annual third column (FY2023) vs the FY2024 prior column.
  E. Plan sanity: old values == live master, apply contract counts, owner-gold cells == the approved list (class evidence), no planned cell would be a masked gold cell.
Writes kr0072_verify.txt / kr0072_verify.json next to this file; exit code 1 when anything fails.
Env: KR0072_PLAN (plan json, default e23_plan_kdb.json) | KR0072_MUTATE (col|line|tbl|val|unit) | KR0072_OUTTAG | KR0072_BASE (root of the pre-load masters; default = repo root = before the load)."""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from kdb_notes import CSM_CORE, csm_tables, first_text_above, numeric_cells, pl4_note  # noqa: E402
from kdb_raw import ROOT, all_tables, clean, close, lines_of, mn, nspace, parse_num, section, table_rows, table_unit  # noqa: E402
from kdb_stmt import LABELS, Stmt, identities, items_from  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((HERE / os.environ.get("KR0072_PLAN", "e23_plan_kdb.json")).read_text(encoding="utf-8"))
MUTATE = os.environ.get("KR0072_MUTATE", "")
OUTTAG = os.environ.get("KR0072_OUTTAG", "")
BASE = Path(os.environ.get("KR0072_BASE", str(ROOT)))
CODE = "KR0072"
PROBLEMS, OUT, RES = [], [], {}

DART = "data/dart"
F = dict(
    N1=f"{DART}/FY2024_Q1/raw/KR0072_케이디비생명보험/20240516000597.xml",
    N2=f"{DART}/FY2024_Q2/raw/KR0072_케이디비생명보험/20240814000801.xml",
    N3=f"{DART}/FY2024_Q3/raw/KR0072_케이디비생명보험/20241114000809.xml",
    N4=f"{DART}/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302.xml",
    N4AUD=f"{DART}/FY2024_Q4/raw/KR0072_케이디비생명보험_20250331002302/20250331002302_00760.xml",
    O1=f"{DART}/FY2023_Q1/raw/KR0072_케이디비생명보험/xml/20230515002450.xml",
    O2=f"{DART}/FY2023_Q2/raw/KR0072_케이디비생명보험/xml/20230814003052.xml",
    O3=f"{DART}/FY2023_Q3/raw/KR0072_케이디비생명보험/xml/20231114002983.xml",
    O4=f"{DART}/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/20240401002710.xml",
    O4AUD=f"{DART}/FY2023_Q4/raw/KR0072_케이디비생명보험_20240401002710/xml/20240401002710_00760.xml",
    A25=f"{DART}/FY2025_Q4/raw/KR0072_케이디비생명보험_20260331004180/20260331004180.xml",
)
QUARTERS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]
NEWKEY = {"2023.1Q": "N1", "2023.2Q": "N2", "2023.3Q": "N3", "2023.4Q": "N4"}
OLDKEY = {"2023.1Q": "O1", "2023.2Q": "O2", "2023.3Q": "O3", "2023.4Q": "O4"}
APPROVED_PL_GOLD = {("2023.2Q", 4), ("2023.2Q", 7), ("2023.3Q", 4), ("2023.3Q", 7)}
APPROVED_CSM_GOLD_A = {("2023.1Q", 4), ("2023.1Q", 5), ("2023.1Q", 6), ("2023.2Q", 4), ("2023.2Q", 5)}
APPROVED_CSM_GOLD_B = {("2023.4Q", 1), ("2023.4Q", 4)}
MASK_TOL = 0.05          # gold_overlay_verdict: |gold - builder source| <= 0.05 -> SAME_AT_1DP (masked); <= 0.005 SAME_EXACT   (scripts/validate_data_contract.py GOLD_OVERLAY_TOL_*)


def say(s=""):
    OUT.append(s)
    print(s)


def problem(where, msg):
    PROBLEMS.append(dict(where=where, problem=msg))
    say(f"  !! PROBLEM [{where}] {msg}")


def sha12(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:12]


def load_masters(base):
    pl = json.loads((base / "PL_breakdown.json").read_text(encoding="utf-8"))
    cs = json.loads((base / "CSM_waterfall.json").read_text(encoding="utf-8"))
    gold = json.loads((base / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
    cgold = json.loads((base / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
    return pl, cs, gold, cgold


# ------------------------------------------------------------------------------------------------ old-layout (roman numeral) statements of the ORIGINAL 2023.1Q / 2023.2Q filings
def core_label(s):
    s = nspace(re.sub(r"\(주[^)]*\)", "", s))
    return re.sub(r"^([IVXlL]+\.|\d+\.)", "", s)


class OldStmt:
    """original FY2023 1Q / 2Q separate statement ('4. 재무제표', old layout): header '과 목 | 제36기 .. | 제35기 ..', rows with roman numerals; Q2 has 3개월 | 누적 pairs for each period, Q1 has detail | subtotal."""

    def __init__(self, key, quarter):
        self.key, self.rel, self.quarter = key, F[key], quarter
        L = self.L = lines_of(self.rel)
        a, b = section(L, r"^4\.\s*재무제표$")
        self.tab = None
        for (ta, tb) in all_tables(L):
            if not (a <= ta <= b):
                continue
            rows = table_rows(L, ta, tb)
            labs = {core_label(r["cells"][0]["text"]) for r in rows if r["cells"]}
            if "영업이익" in labs and ("법인세비용차감전순이익" in labs) and ("영업수익" in labs):
                self.tab = (ta, tb, rows)
                break
        if self.tab is None:
            raise RuntimeError(f"{self.rel}: old-layout statement not found in {a + 1}..{b + 1}")
        ta, tb, rows = self.tab
        self.unit, self.unit_line, self.unit_where = table_unit(L, ta, tb)
        if self.unit_where != "in" and self.unit is None:
            raise RuntimeError("unit not found")
        self.rows = [r for r in rows if r["cells"] and len(r["cells"]) >= 4]

    def find(self, core, nth=1, section_after=None):
        hits = [(k, r) for k, r in enumerate(self.rows) if core_label(r["cells"][0]["text"]) == core]
        if section_after is not None:
            hits = [(k, r) for k, r in hits if k > section_after]
        if len(hits) < nth:
            raise RuntimeError(f"{self.rel}: old-layout row {core!r} nth={nth}: {len(hits)} hits")
        return hits[nth - 1]

    def val(self, core, which="cur", nth=1, section_after=None):
        """-> dict(printed, line, mn, label, label_line, rowidx).  Q2: columns [3m, cum, prior 3m, prior cum] -> cur cum = 2nd; Q1: [cur detail, cur subtotal, prior detail, prior subtotal]."""
        k, r = self.find(core, nth, section_after)
        cs = r["cells"][1:]
        if self.quarter == "2023.2Q":
            idx = {"cur": 1, "cur3m": 0, "prior": 3, "prior3m": 2}[which]
            c = cs[idx]
        else:
            pair = cs[0:2] if which == "cur" else cs[2:4]
            c = pair[0] if pair[0]["text"] != "" else pair[1]
        return dict(printed=c["text"], line=c["line"], mn=mn(c["text"], self.unit) if c["text"] != "" else None, label=r["cells"][0]["text"], label_line=r["cells"][0]["line"], rowidx=k)


def old_items(O):
    """live-master-style items (백만원) from the old-layout statement (cumulative, current period):
    3 = 보험영업수익 - 보험영업비용, 8 = 재보험영업수익 - 재보험영업비용, 2 = 3 + 8, 16 = 기타사업비용, 19 = 보험금융수익(수익 8.) - 보험금융비용(비용 8.), 20/22/24 = subtotal rows, 21 = 영업외수익 - 영업외비용, 23 = 법인세수익 row as printed."""
    exp_start = O.find("영업비용")[0]
    g = lambda core, **kw: O.val(core, "cur", **kw)  # noqa: E731
    rev = g("보험영업수익")
    rerev = g("재보험영업수익")
    cost = g("보험영업비용")
    recost = g("재보험영업비용")
    oc = g("기타사업비용")
    finrev = g("보험금융수익")
    fincost = g("보험금융비용")
    op = g("영업이익")
    nonrev = g("영업외수익")
    noncost = g("영업외비용")
    pretax = g("법인세비용차감전순이익")
    taxr = O.val("법인세수익", "cur")
    ni = g("분기순이익") if O.quarter == "2023.1Q" else g("반기순이익")
    it = {3: rev["mn"] - cost["mn"], 8: rerev["mn"] - recost["mn"], 16: oc["mn"], 19: finrev["mn"] - fincost["mn"], 20: op["mn"], 21: nonrev["mn"] - noncost["mn"], 22: pretax["mn"], 23: taxr["mn"], 24: ni["mn"]}
    it[2] = it[3] + it[8]
    cites = dict(rev=rev, rerev=rerev, cost=cost, recost=recost, oc=oc, finrev=finrev, fincost=fincost, op=op, nonrev=nonrev, noncost=noncost, pretax=pretax, tax=taxr, ni=ni)
    return it, cites


# ------------------------------------------------------------------------------------------------ original 2023.1Q CSM table (first-IFRS17 quarter layout, 2-level row labels)
def o1_csm_cur(rel):
    """the issued-contract insurance-service roll-forward of the ORIGINAL 2023.1Q filing (separate notes), 'cur' period: rows by label, CSM = 3rd value column.  Selected by the two text lines above the table
    ('(3) 당분기와 전기 중 발행한 보험계약의 보험서비스와 관련된 항목...' + '1) 제36(당)기 1분기') and the header 구분 | 미래현금흐름에 대한 추정치 | 위험조정 | 보험계약마진 | 합계."""
    L = lines_of(rel)
    lo, hi = section(L, r"^5\.\s*재무제표 주석")
    hits = []
    for (ta, tb) in all_tables(L):
        if not (lo <= ta <= hi):
            continue
        ln1, t1 = first_text_above(L, ta)
        if not (t1 or "").startswith("1) 제36(당)기 1분기"):
            continue
        ln2, t2 = first_text_above(L, ln1 - 1)
        if "발행한 보험계약의 보험서비스와 관련된 항목" not in (t2 or ""):
            continue
        rows = table_rows(L, ta, tb)
        hdr = next((r for r in rows if r["cells"] and nspace(r["cells"][0]["text"]) == "구분"), None)
        if hdr is None or [nspace(c["text"]) for c in hdr["cells"][1:]] != ["미래현금흐름에대한추정치", "위험조정", "보험계약마진", "합계"]:
            continue
        hits.append((ta, tb, rows))
    if len(hits) != 1:
        raise RuntimeError(f"{rel}: {len(hits)} original 2023.1Q issued insurance-service roll-forward tables")
    ta, tb, rows = hits[0]
    un, unl, uw = table_unit(L, ta, tb)
    res = {}
    for r in rows:
        cs = r["cells"]
        if len(cs) < 5 or parse_num(cs[-1]["text"]) is None:
            continue
        labels = [nspace(c["text"]) for c in cs[:-4]]
        vals = cs[-4:]
        csm = vals[2]
        key = None
        if labels == ["기초잔액"]:
            key = 1
        elif labels == ["해당기간에처음인식한계약의효과"]:
            key = 2
        elif labels == ["보험금융비용", "당기손익"]:
            key = 3
        elif labels and labels[-1] == "보험계약마진을조정하는추정치의변동분":
            key = 4
        elif labels and labels[-1] == "서비스제공으로당기손익으로인식된보험계약마진":
            key = 5
        elif labels == ["분기말잔액"]:
            key = 6
        if key is not None:
            if key in res:
                raise RuntimeError(f"{rel}: duplicate original 2023.1Q CSM row {key}")
            res[key] = dict(label=" / ".join(c["text"] for c in cs[:-4]), label_line=cs[0]["line"], printed=csm["text"], line=csm["line"], mn=mn(csm["text"], un))
    if sorted(res) != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError(f"{rel}: original 2023.1Q CSM rows found {sorted(res)}")
    return dict(rows=res, table=(ta + 1, tb + 1), unit=un, unit_where=uw)


def fy_column_rows(rel, header_text):
    """[(normalised label, value in 원 as float, 1-based line)] of the separate 4-2 statement for the column whose header cell reads `header_text` (no THEAD needed: header cells are found among the first rows)"""
    L = lines_of(rel)
    a, b = section(L, r"^4-2\.\s*포괄손익계산서")
    tab = None
    for (ta, tb) in all_tables(L):
        if a <= ta <= b:
            rows = table_rows(L, ta, tb)
            if any(nspace(r["cells"][0]["text"]) == "보험손익" for r in rows if r["cells"]):
                tab = (ta, tb, rows)
                break
    ta, tb, rows = tab
    hdr_idx = None
    for r in rows[:8]:
        texts = [c["text"] for c in r["cells"]]
        if header_text in texts and len(texts) >= 3:
            hdr_idx = texts.index(header_text)
            break
    if hdr_idx is None:
        # THEAD paths
        from kdb_raw import header_paths
        paths = header_paths(L, ta, tb)
        hdr_idx = next(j for j, p_ in enumerate(paths) if p_ and p_[0] == header_text)
    out = []
    for r in rows:
        cs = r["cells"]
        if len(cs) > hdr_idx and hdr_idx > 0:
            v = parse_num(cs[hdr_idx]["text"])
            if v is not None and cs[hdr_idx]["text"] != "" and nspace(cs[0]["text"]) != "":
                out.append((nspace(cs[0]["text"]), v, cs[hdr_idx]["line"]))
    return out


def eok(v_mn):
    return None if v_mn is None else v_mn / 100.0


def r2(x):
    return round(x + 0.0, 2)


# ------------------------------------------------------------------------------------------------ main
def main():
    pl_rows, csm_rows, gold, cgold = load_masters(BASE)
    LIVE = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_rows}
    LIVEC = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_rows}
    GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
    GOLDC = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in cgold["set"]}
    # builder sources (fresh, no gold) for the 'masked gold cell' test
    src_pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))}
    src_csm = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))}
    say(f"KR0072 independent re-read | plan {PLAN.get('scenario')} | masters from {BASE} | mutation '{MUTATE}'")
    say("input hashes: " + ", ".join(f"{k}={sha12(v)}" for k, v in F.items() if (ROOT / v).exists()))

    # ================================================================ B. candidate re-read
    say("\n== B. CANDIDATE: FY2024 filings, separate 4-2 statement, prior-year (2023) cumulative column, read with the production definitions")
    NEW = {}
    year = 2024 if MUTATE == "col" else 2023
    for q in QUARTERS:
        S = Stmt(F[NEWKEY[q]])
        V = S.read(year, "cum")
        it = items_from(V)
        n4 = pl4_note(F[NEWKEY[q]], "cur" if MUTATE == "col" else "prior")
        it[4] = n4["mn"]
        # plugs: 7 = 3 - (4 + 5 + 6), 12 = 8 - (9 + 10 + 11) with the live legs (the plan keeps legs 5 / 6 / 9 / 10 / 11 at the live values)
        legs = {i: LIVE.get((CODE, i, q)) for i in (5, 6, 9, 10, 11)}
        if all(legs[i] is not None and legs[i]["값"] is not None for i in (5, 6)):
            it[7] = it[3] - (it[4] + legs[5]["값"] + legs[6]["값"])
        if all(legs[i] is not None and legs[i]["값"] is not None for i in (9, 10, 11)):
            it[12] = it[8] - (legs[9]["값"] + legs[10]["값"] + legs[11]["값"])
        NEW[q] = dict(S=S, V=V, items=it, n4=n4)
        hdr = V["ins_result"]["header"]
        ordinal = int(re.search(r"제\s*(\d+)", hdr[0]).group(1))
        ptxt = S.periods[ordinal]["text"]
        say(f"  {q}: {S.rel} | unit {S.unit} (line {S.unit_line}) | column {V['ins_result']['col']} header {hdr} | period header (L{S.periods[ordinal]['line']}) {ptxt}")
        if S.unit != "원":
            problem(f"{q}", f"statement unit {S.unit}")
        if MUTATE == "unit":
            pass

    CSMN = {}
    for q in QUARTERS:
        T = csm_tables(F[NEWKEY[q]])
        role = "cur" if MUTATE == "tbl" else "prior"
        if sorted(k for k in T if k) != ["cur", "prior"] or None in T:
            problem(f"{q} CSM", f"expected exactly one cur and one prior issued CSM table, got {list(T)}")
        CSMN[q] = T[role]
    say("  PL4 (CSM amortisation, 백만원): 구성내역 note (prior cumulative) | CSM roll-forward row 5 (prior table)")
    for q in QUARTERS:
        n4, c5 = NEW[q]["n4"], -CSMN[q]["rows"][5]["mn"]
        ok = n4["mn"] == c5
        extra = f" | prior 3개월 {n4['prior_3m']['printed']} (L{n4['prior_3m']['line']})" if "prior_3m" in n4 else ""
        say(f"    {q}: note {n4['printed']} (L{n4['line']}, table L{n4['table'][0]}, {n4['n_numeric']} numeric cells, unit {n4['unit']} {n4['unit_where']}-table){extra} | roll-forward row 5 {CSMN[q]['rows'][5]['printed']} (L{CSMN[q]['rows'][5]['line']}) -> {'AGREE' if ok else 'DISAGREE'}")
        if not ok:
            problem(f"{q} PL4", "CSM amortisation differs between the 구성내역 note and the roll-forward")
        if n4["unit_where"] != "in" or CSMN[q]["unit_where"] != "in" or n4["unit"] != "백만원" or CSMN[q]["unit"] != "백만원":
            problem(f"{q} unit", f"note unit {n4['unit']}/{n4['unit_where']} csm unit {CSMN[q]['unit']}/{CSMN[q]['unit_where']}")

    # ---------------------------------------------------------------- B1. every planned PL cell
    say("\n== B1. every planned PL cell: value, unit, sign, row label, physical line of each part")
    n_ok = n_cells = 0
    plan_pl = {}
    for b in PLAN["buckets"]:
        q = b["quarter"]
        mine = NEW[q]["items"]
        S = NEW[q]["S"]
        V = NEW[q]["V"]
        jcol = V["ins_result"]["col"]
        by_line = {}
        for k, r in enumerate(S.rows):
            cs = r["cells"]
            if len(cs) == len(S.paths):
                for j, c in enumerate(cs):
                    if j > 0:
                        by_line[c["line"]] = (k, j, cs[0]["text"], c["text"])
        if b["meta"]["file"] != F[NEWKEY[q]]:
            problem(f"{q}", f"plan source file {b['meta']['file']} != {F[NEWKEY[q]]}")
        for c in b["cells"]:
            n_cells += 1
            item = c["item"]
            plan_pl[(q, item)] = c
            mv = mine.get(item)
            pv = c["new"] + (1.0 if MUTATE == "val" and q == "2023.2Q" and item == 20 else 0.0)
            msgs = []
            if not close(mv, pv, 2e-6):
                msgs.append(f"value plan {pv} != re-read {mv}")
            if c["unit"] != "백만원":
                msgs.append(f"unit {c['unit']}")
            tot = 0.0
            for p in c["parts"]:
                ln = p["line"] + (1 if MUTATE == "line" and q == "2023.1Q" and item == 1 else 0)
                if item == 4:
                    ref = NEW[q]["n4"]
                    if not (ln == ref["line"] and p["printed"] == ref["printed"] and p["unit"] == ref["unit"] and nspace(p["label"]).startswith(nspace("(3) 제공된 서비스의 보험계약마진"))):
                        msgs.append(f"PL4 part L{ln} {p['printed']} {p['unit']} {p['label']!r} != note L{ref['line']} {ref['printed']} {ref['unit']}")
                    if not close(p["contribution_mn"], ref["mn"]):
                        msgs.append("PL4 contribution")
                    tot += p["contribution_mn"]
                    continue
                hit = by_line.get(ln)
                if hit is None:
                    msgs.append(f"part line {ln} is not a statement value cell")
                    continue
                k, j, lab, printed = hit
                if nspace(lab) != nspace(p["label"]):
                    msgs.append(f"part L{ln}: label {p['label']!r} != row label {lab!r}")
                if j != jcol:
                    msgs.append(f"part L{ln} sits in column {j}, the prior-year cumulative column is {jcol}")
                if printed != p["printed"]:
                    msgs.append(f"part L{ln}: printed {p['printed']} != {printed}")
                if p["unit"] != S.unit:
                    msgs.append(f"part L{ln}: unit {p['unit']} != {S.unit}")
                mnv = mn(printed, S.unit)
                expect = p["sign"] * (abs(mnv) if p["abs"] else mnv)
                if not close(p["contribution_mn"], expect):
                    msgs.append(f"part L{ln}: contribution {p['contribution_mn']} != sign*{'|x|' if p['abs'] else 'x'} {expect}")
                tot += p["contribution_mn"]
            for o in c.get("operands", []):
                lv = LIVE.get((CODE, o["item"], q))
                if o["source"] == "plan":
                    ok_o = close(mine.get(o["item"]), o["value"], 2e-6)
                else:
                    ok_o = lv is not None and close(lv["값"], o["value"], 1e-6)
                if not ok_o:
                    msgs.append(f"operand item {o['item']} {o['value']} ({o['source']}): live {None if lv is None else lv['값']} / re-read {mine.get(o['item'])}")
                tot += o["sign"] * o["value"]
            if c["parts"] and not close(tot, pv, 5e-6):
                msgs.append(f"sum of parts+operands {tot} != cell {pv}")
            if item == 15:
                absent = not any(nspace(r["cells"][0]["text"]) == "기타영업수익" for r in S.rows)
                if not (absent and close(pv, 0.0)):
                    msgs.append("item 15: a 기타영업수익 row exists or value != 0.0")
            if msgs:
                problem(f"{q} i{item}", "; ".join(msgs))
            else:
                n_ok += 1
    say(f"  planned PL cells {n_cells}, fully matching the independent re-read: {n_ok}")
    RES["pl_cells"], RES["pl_cells_ok"] = n_cells, n_ok

    # N4: XBRL context of the cited annual cells = prior fiscal year 2023 on the SEPARATE basis
    S4 = NEW["2023.4Q"]["S"]
    bad_ctx = 0
    for b in PLAN["buckets"]:
        if b["quarter"] != "2023.4Q":
            continue
        for c in b["cells"]:
            for p in c["parts"]:
                if "line" not in p or p.get("unit") != "원":
                    continue
                cell = None
                for r in S4.rows:
                    for cc in r["cells"]:
                        if cc["line"] == p["line"]:
                            cell = cc
                if cell is None or "PFY2023dFY" not in cell["attrs"] or "SeparateMember" not in cell["attrs"]:
                    bad_ctx += 1
                    problem("2023.4Q ctx", f"item {c['item']} L{p['line']}: XBRL context is not PFY2023dFY + SeparateMember")
    say(f"  2023.4Q cited cells carry ACONTEXT PFY2023dFY ... SeparateMember (XBRL prior fiscal year, separate basis): {'all' if not bad_ctx else str(bad_ctx) + ' DO NOT'}")

    # ---------------------------------------------------------------- B2. completeness + mask test
    say("\n== B2. completeness: items re-read from the filing but NOT in the plan (live master vs re-read) and the 'masked gold cell' test against the builder source")
    for q in QUARTERS:
        for item in sorted(NEW[q]["items"]):
            if (q, item) in plan_pl:
                continue
            lv = LIVE.get((CODE, item, q))
            lvv = None if lv is None else lv["값"]
            mv = NEW[q]["items"][item]
            if lvv is None:
                if item in (5, 6, 9, 10, 11, 13, 14):
                    continue
                problem(f"{q} i{item}", f"re-read value {mv} but the live master is blank and the plan skips it (fill missing)")
                continue
            d = mv - lvv
            cls = "equal" if abs(d) <= 2e-5 else ("rounding" if abs(d) <= 1.0001 else "DIFFERENT")
            note = ""
            if cls == "rounding":
                sv = src_pl.get((CODE, item, q), {}).get("값")
                masked = sv is not None and abs(mv - sv) <= MASK_TOL
                note = f" | builder source {sv} -> a gold cell of {mv:.6f} would be {'MASKED (needs a ledger pin)' if masked else 'NOT masked'}"
                if not masked:
                    problem(f"{q} i{item}", f"rounding-only difference that is NOT excluded for a mask reason: {note}")
            say(f"  {q} i{item:>2}: live {lvv:>16,.6f} re-read {mv:>16,.6f} diff {d:+.6f} -> {cls}{note}")
            if cls == "DIFFERENT":
                problem(f"{q} i{item}", f"not in the plan but live {lvv} != re-read {mv}")
    n_mask_bad = 0
    for (q, item), c in sorted(plan_pl.items()):
        sv = src_pl.get((CODE, item, q), {}).get("값")
        if sv is not None and abs(c["new"] - sv) <= MASK_TOL:
            n_mask_bad += 1
            problem(f"{q} i{item}", f"planned cell {c['new']} is within {MASK_TOL} of the builder source {sv}: it would be a masked gold cell")
    say(f"  planned PL cells that would be masked gold cells (|new - builder source| <= {MASK_TOL}): {n_mask_bad}")

    # ---------------------------------------------------------------- B3. issuer's own statement about restatement
    say("\n== B3. issuer statement on restatement in the FY2024 filings (information)")
    for key in ("N1", "N2", "N3", "N4"):
        L = lines_of(F[key])
        for k, s in enumerate(L):
            if "재무제표 재작성 등 유의사항" in s:
                txt = clean(" ".join(L[k:k + 3]))
                say(f"  {key} L{k + 1}: {txt[:170]}")
                break

    # ---------------------------------------------------------------- B4. CSM cells
    say("\n== B4. every planned CSM cell: stored value (억원), exact 2-decimal value, label, line, printed")
    n_c = n_c_ok = 0
    plan_csm = {}
    for cb in PLAN["csm_buckets"]:
        q = cb["quarter"]
        T = CSMN[q]
        if not cb["file"].startswith(F[NEWKEY[q]]):
            problem(f"{q} CSM", f"plan file {cb['file']} != {F[NEWKEY[q]]}")
        if cb["file"].split("table@L")[1].split(" ")[0] != str(T["table"][0]):
            problem(f"{q} CSM", f"plan table {cb['file']} != re-read table L{T['table'][0]}")
        # the stored precision of the bucket: 2 decimals when any CSM gold cell of the bucket (pre-load) holds a 2-decimal value, else 1
        two_dp = any((CODE, i, q) in GOLDC and abs(round(GOLDC[(CODE, i, q)]["값"], 1) - GOLDC[(CODE, i, q)]["값"]) > 1e-9 for i in range(1, 7))
        if two_dp != bool(cb["two_dp"]):
            problem(f"{q} CSM", f"stored precision: plan two_dp={cb['two_dp']} vs pre-load gold evidence {two_dp}")
        for c in cb["cells"]:
            n_c += 1
            i = c["item"]
            plan_csm[(q, i)] = c
            r = T["rows"][i]
            exact = r2(r["mn"] / 100.0)
            stored = exact if two_dp else round(exact, 1)
            pv = c["new"] + (0.1 if MUTATE == "val" and q == "2023.3Q" and i == 6 else 0.0)
            msgs = []
            if abs(stored - pv) > 1e-9:
                msgs.append(f"stored plan {pv} != re-read {stored} (exact {exact}, two_dp {two_dp})")
            if abs(exact - c["exact"]) > 1e-9:
                msgs.append(f"exact plan {c['exact']} != {exact}")
            for p in c["parts"]:
                ln = p["line"] + (1 if MUTATE == "line" and q == "2023.1Q" and i == 1 else 0)
                if ln != r["line"] or p["printed"] != r["printed"]:
                    msgs.append(f"part L{ln} {p['printed']} != re-read L{r['line']} {r['printed']}")
                if nspace(p["label"]) != nspace(r["label"]):
                    msgs.append(f"label {p['label']!r} != {r['label']!r}")
                if p["unit"] != "백만원" or T["unit"] != "백만원":
                    msgs.append(f"unit {p['unit']} / table {T['unit']}")
                if abs(p["contribution_eok"] - exact) > 1e-9:
                    msgs.append(f"part contribution {p['contribution_eok']} != {exact}")
            if T["unit"] != "백만원" or T["unit_where"] != "in" or (MUTATE == "unit" and q == "2023.1Q"):
                msgs.append(f"table unit {T['unit']} ({T['unit_where']})")
            if msgs:
                problem(f"{q} CSM i{i}", "; ".join(msgs))
            else:
                n_c_ok += 1
    say(f"  planned CSM cells {n_c}, fully matching the independent re-read: {n_c_ok}")
    RES["csm_cells"], RES["csm_cells_ok"] = n_c, n_c_ok
    for q in QUARTERS:
        for i in range(1, 7):
            if (q, i) in plan_csm:
                continue
            lv = LIVEC.get((CODE, i, q))
            two_dp = any((CODE, j, q) in GOLDC and abs(round(GOLDC[(CODE, j, q)]["값"], 1) - GOLDC[(CODE, j, q)]["값"]) > 1e-9 for j in range(1, 7))
            exact = r2(CSMN[q]["rows"][i]["mn"] / 100.0)
            stored = exact if two_dp else round(exact, 1)
            tol = 0.0051 if (abs(round(lv["값"], 1) - lv["값"]) > 1e-9) else 0.0501
            ok = abs(lv["값"] - stored) <= tol
            say(f"  {q} CSM i{i}: not in the plan, live {lv['값']} vs re-read {stored} (tol {tol}) -> {'equal within the print rounding' if ok else 'DIFFERENT'}")
            if not ok:
                problem(f"{q} CSM i{i}", f"not in the plan but live {lv['값']} != re-read {stored}")
    say("\n  CSM roll-forward closure (printed, 백만원) and stored (억원):")
    for q in QUARTERS:
        v = [CSMN[q]["rows"][i]["mn"] for i in range(1, 7)]
        res = v[0] + v[1] + v[2] + v[3] + v[4] - v[5]
        e = CSMN[q]["extra"]
        grp = e["future"]["mn"] + e["current"]["mn"] + e["past"]["mn"]
        res2 = e["isr"]["mn"] - grp
        res3 = e["fin_pl"]["mn"] + e["fin_oci"]["mn"] - v[2]
        say(f"    {q}: printed {v} closure residual (1+2+3+4+5-6) {res:+.1f} 백만원 | 5.보험서비스결과 {e['isr']['printed']} vs 2+3+4 {grp:+.0f}: {res2:+.0f} | 6. 보험금융손익 {v[2]:.0f} vs (1)+(2) -> {res3:+.0f}")
        if abs(res) > 1.0001 or abs(res2) > 1.0001 or abs(res3) > 1.0001:
            problem(f"{q} CSM", f"printed roll-forward does not close within print rounding ({res}, {res2}, {res3})")
    opens = {q: CSMN[q]["rows"][1]["mn"] for q in QUARTERS}
    say(f"    FY2023 opening per quarter (백만원): {opens} -> {'ONE vintage' if len(set(opens.values())) == 1 else 'MIXED'}")
    if len(set(opens.values())) != 1:
        problem("FY2023 CSM", "openings differ within the FY")
    n1c = csm_tables(F["N1"])["cur"]["rows"][1]
    say(f"    FY boundary: 2023.4Q closing {CSMN['2023.4Q']['rows'][6]['printed']} (L{CSMN['2023.4Q']['rows'][6]['line']}) == FY2024 Q1 opening {n1c['printed']} (L{n1c['line']}) -> {'EQUAL' if CSMN['2023.4Q']['rows'][6]['mn'] == n1c['mn'] else 'BREAK'}")
    if CSMN["2023.4Q"]["rows"][6]["mn"] != n1c["mn"]:
        problem("FY boundary", "2023.4Q closing != 2024.1Q opening")

    # ================================================================ C. identities
    say("\n== C. statement identities from freshly read printed cells (백만원)")
    for q in QUARTERS:
        for name, d, ok in identities(NEW[q]["V"]):
            say(f"  {q} {name}: {d:+.6f} {'OK' if ok else 'FAIL'}")
            if not ok:
                problem(f"{q} identity", f"{name} residual {d}")
        it = NEW[q]["items"]
        br = it[2] + it[15] - it[16] - it[1]
        say(f"  {q} bridge item1 = item2 + item15 - item16: residual {br:+.6f}")
        if abs(br) > 5e-6:
            problem(f"{q} bridge", f"item1 vs item2+item15-item16 residual {br}")
        c25 = it[25] - (it[26] + it[27] + it[28] + it[29] + it[30] + it[32])
        if abs(c25) > 5e-6:
            problem(f"{q} oci", f"item25 vs components residual {c25}")
        c18 = it[17] - it[18] - it[19]
        if abs(c18) > 5e-6:
            problem(f"{q} i17", f"17 != 18 + 19 ({c18})")
        c20 = it[20] - it[1] - it[17]
        if abs(c20) > 5e-6:
            problem(f"{q} i20", f"20 != 1 + 17 ({c20})")
        say(f"  {q} 25 = 26+27+28+29+30+32: {c25:+.6f} | 17 = 18+19: {c18:+.6f} | 20 = 1+17: {c20:+.6f}")

    say("\n== C2. second source for the annual: audit report attachment 20250331002302_00760.xml (separate FS)")
    try:
        Ta = csm_tables(F["N4AUD"], 0, len(lines_of(F["N4AUD"])) - 1)
        rowsA = Ta["prior"]["rows"]
        same = all(rowsA[i]["mn"] == CSMN["2023.4Q"]["rows"][i]["mn"] for i in range(1, 7))
        say(f"  CSM prior table of the attachment (L{Ta['prior']['table'][0]}): {[rowsA[i]['printed'] for i in range(1, 7)]} lines {[rowsA[i]['line'] for i in range(1, 7)]} -> {'EQUAL to the main document' if same else 'DIFFERENT'}")
        if not same:
            problem("N4AUD", "CSM prior table differs from the main document")
    except Exception as e:  # noqa
        problem("N4AUD", f"could not read the attachment CSM table: {e}")
    try:
        To = csm_tables(F["O4AUD"], 0, len(lines_of(F["O4AUD"])) - 1)
        rowsO = To["cur"]["rows"]
        same = all(rowsO[i]["mn"] == CSMN["2023.4Q"]["rows"][i]["mn"] for i in range(1, 7))
        say(f"  original FY2023 annual attachment (rcept 20240401002710_00760) CSM current table L{To['cur']['table'][0]}: {[rowsO[i]['printed'] for i in range(1, 7)]} -> {'EQUAL to the FY2024 prior column' if same else 'DIFFERENT'}")
        if not same:
            problem("O4AUD", "original annual CSM current table differs from the FY2024 prior column")
    except Exception as e:  # noqa
        problem("O4AUD", f"could not read the original annual attachment CSM table: {e}")

    # ================================================================ D. seams
    say("\n== D. SEAM evidence")
    say("  D1 single quarter derived from the cumulatives as they will stand in the master (new where planned, live otherwise) vs the printed 3-month column of the same filing (백만원):")
    contract = PLAN["apply_contract"]
    planned_set = {(s[1], s[2]): s for s in contract["set_dangi_add"]}
    seam_mine = {}
    for q, prevq in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
        S = NEW[q]["S"]
        V3 = S.read(2023, "3m")
        v3 = items_from(V3)
        for item in sorted(v3):
            if item in (15, 4):
                continue
            def after(qq, it_):
                c = plan_pl.get((qq, it_))
                if c is not None:
                    return c["new"]
                lvx = LIVE.get((CODE, it_, qq))
                return None if lvx is None else lvx["값"]
            if (q, item) not in plan_pl and (prevq, item) not in plan_pl:
                continue          # neither cumulative changes in this load -> the single quarter is untouched
            cur, prev = after(q, item), after(prevq, item)
            if cur is None or prev is None:
                continue
            derived = cur - prev
            d = derived - v3[item]
            tol = 3 * 2e-5
            if abs(d) > tol:
                seam_mine[(q, item)] = (derived, v3[item], d)
    for (q, item), (der, p3, d) in sorted(seam_mine.items()):
        say(f"    {q} i{item:>2}: derived {der:>16,.6f} printed 3m {p3:>16,.6f} diff {d:+.6f} -> seam (set_dangi proposed by the plan: {(q, item) in planned_set})")
    if set(seam_mine) != set(planned_set):
        problem("seams", f"my seam set {sorted(seam_mine)} != planned set_dangi {sorted(planned_set)}")
    for (q, item), s in planned_set.items():
        mine3 = seam_mine.get((q, item))
        if mine3 is not None and abs(float(s[3]) - mine3[1]) > 1e-6:
            problem(f"{q} i{item}", f"planned set_dangi value {s[3]} != printed 3-month {mine3[1]}")
        txt = s[4]
        m = re.search(r"L(\d+) \[", txt)
        if m is None:
            problem(f"{q} i{item}", "set_dangi source text has no line citation")
        else:
            ln = int(m.group(1))
            S = NEW[q]["S"]
            col3 = NEW[q]["S"].col(2023, "3m")
            cell = None
            for r in S.rows:
                for cc in r["cells"]:
                    if cc["line"] == ln:
                        cell = (r["cells"][0]["text"], cc["text"], r["cells"].index(cc))
            if cell is None or cell[2] != col3:
                problem(f"{q} i{item}", f"set_dangi cited line {ln} is not a prior-year 3개월 cell ({cell})")
            else:
                say(f"      cite check {q} i{item}: L{ln} row '{cell[0]}' printed {cell[1]} in the prior-year 3개월 column {col3}")
    n_cons = 0
    for q, prevq in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
        v3 = items_from(NEW[q]["S"].read(2023, "3m"))
        n_cons += sum(1 for it_ in v3 if it_ not in (15, 4) and (q, it_) not in seam_mine and plan_pl.get((q, it_)) is not None)
    say(f"    items whose derived single quarter equals the printed 3-month column to the print precision: {n_cons} planned item-quarters (the rest are the seams above or have no previous-quarter cumulative)")
    # the 'second restatement' behind the 2023.3Q seams: the 6 months implied by the Q3 report vs the 6 months printed in the Q2 report
    say("    explanation of the 2023.3Q seams: 6M implied by the FY2024 Q3 report (9M cumulative - 3개월) vs 6M printed in the FY2024 Q2 report:")
    V9, V3q, V6 = NEW["2023.3Q"]["V"], NEW["2023.3Q"]["S"].read(2023, "3m"), NEW["2023.2Q"]["V"]
    i9, i3, i6 = items_from(V9), items_from(V3q), items_from(V6)
    for item in (1, 17, 18, 19, 20, 22, 24, 25, 31):
        implied = i9[item] - i3[item]
        say(f"      i{item:>2}: implied 6M {implied:>16,.6f} | printed 6M {i6[item]:>16,.6f} | diff {implied - i6[item]:+.6f}")
    # PL4 single quarter: the note prints 3개월 columns in the half-year / third-quarter reports
    for q, prevq in (("2023.2Q", "2023.1Q"), ("2023.3Q", "2023.2Q")):
        n4 = NEW[q]["n4"]
        derived = NEW[q]["items"][4] - NEW[prevq]["items"][4]
        p3 = n4["prior_3m"]["mn"]
        say(f"    PL4 {q}: derived {derived:,.0f} vs printed prior 3개월 {n4['prior_3m']['printed']} (L{n4['prior_3m']['line']}) diff {derived - p3:+.0f} (print rounding of 백만원 sums)")
        if abs(derived - p3) > 1.0001:
            problem(f"{q} PL4 seam", f"derived {derived} vs printed {p3}")
    say("  D2 FY2025 annual report (rcept 20260331004180) third column (제 36 기 = FY2023) vs the FY2024 annual prior column:")
    a25 = fy_column_rows(F["A25"], "제 36 기")
    n4c = fy_column_rows(F["N4"], "제 36 기")
    shift = {nspace("보험비용"): nspace("보험서비스비용"), nspace("보험서비스비용"): nspace("보험영업비용"), nspace("영업이익"): nspace("영업이익(손실)"),
             nspace("법인세차감전순이익"): nspace("법인세비용차감전순이익(손실)"), nspace("법인세수익"): nspace("법인세비용(수익)"), nspace("당기순이익"): nspace("당기순이익(손실)")}
    pool = list(a25)
    n_match, n_renamed, n_zero_gone, unmatched = 0, 0, 0, []
    rest = []
    for lab, val, ln in n4c:
        cands = [lab] + ([shift[lab]] if lab in shift else [])
        hit = next((x for x in pool if x[0] in cands and abs(x[1] - val) <= 1e-9), None)
        if hit is None:
            rest.append((lab, val, ln))
        else:
            pool.remove(hit)
            n_match += 1
    for lab, val, ln in rest:
        hit = next((x for x in pool if abs(x[1] - val) <= 1e-9 and val != 0.0), None)
        if hit is not None:
            pool.remove(hit)
            n_renamed += 1
            say(f"      renamed row (same value to the won): FY2024 annual L{ln} '{lab}' {val:,.0f} == FY2025 annual L{hit[2]} '{hit[0]}'")
        elif val == 0.0:
            n_zero_gone += 1
        else:
            unmatched.append((lab, val, ln))
    say(f"    FY2024 annual prior column rows {len(n4c)} | same label (or shifted label) and same value to the won {n_match} | renamed row with the same value {n_renamed} | zero rows of obsolete labels not reprinted {n_zero_gone} | NOT reproduced {len(unmatched)}")
    for u in unmatched[:12]:
        say(f"      NOT reproduced: {u}")
    key_ok = all(any(abs(x[1] - NEW["2023.4Q"]["V"][k]["mn"] * 1e6) <= 1e-3 for x in a25 if x[0] in {nspace(y) for y in LABELS[k]} | {nspace("영업이익(손실)"), nspace("법인세비용(수익)"), nspace("당기순이익(손실)"), nspace("법인세비용차감전순이익(손실)")}) for k in ("ins_result", "inv", "ni", "oci", "tci"))
    say(f"    key rows (보험손익 투자손익 당기순이익 기타포괄손익 총포괄손익) equal in both: {key_ok} -> {'no later restatement of FY2023' if not unmatched else 'DIFFERENT'}")
    if unmatched:
        problem("A25", f"FY2025 annual third column differs from the FY2024 prior column on {len(unmatched)} rows")

    # ================================================================ A. control (original filings vs the live pre-load master)
    say("\n== A. CONTROL: ORIGINAL FY2023 filings read with the same definitions vs the LIVE (pre-load) master")
    ctrl_bad = 0
    for q in ("2023.3Q", "2023.4Q"):
        S = Stmt(F[OLDKEY[q]])
        V = S.read(2023, "cum")
        it = items_from(V)
        say(f"  {q} original {S.rel} (unit {S.unit}) separate statement, cumulative column:")
        for item in sorted(it):
            if item in (15,):
                lv = LIVE.get((CODE, item, q))
                say(f"     i{item:>2}: live {None if lv is None else lv['값']} (builder default 0.0, no 기타영업수익 row)")
                continue
            lv = LIVE.get((CODE, item, q))
            lvv = None if lv is None else lv["값"]
            if lvv is None:
                say(f"     i{item:>2}: live master blank, original print {it[item]:,.6f}")
                continue
            d = it[item] - lvv
            ok = abs(d) <= 2e-6
            say(f"     i{item:>2}: live {lvv:>16,.6f} original print {it[item]:>16,.6f} diff {d:+.6f} -> {'reproduced' if ok else 'differs'}")
            if not ok:
                ctrl_bad += 1
                problem(f"control {q} i{item}", f"definitions do not reproduce the live master ({it[item]} vs {lvv})")
        n4 = pl4_note(F[OLDKEY[q]], "cur")
        lv4 = LIVE[(CODE, 4, q)]["값"]
        say(f"     i 4: live {lv4:,.1f} original note '(3) 제공된 서비스의 보험계약마진' current cumulative {n4['printed']} (L{n4['line']}) -> {'reproduced' if abs(n4['mn'] - lv4) <= 0.5 else 'differs'}"
            + (" [owner gold]" if (CODE, 4, q) in GOLD else ""))
        if abs(n4["mn"] - lv4) > 0.5:
            ctrl_bad += 1
            problem(f"control {q} i4", "original note does not reproduce the live item 4")
    for q in ("2023.1Q", "2023.2Q"):
        O = OldStmt(OLDKEY[q], q)
        oi, cites = old_items(O)
        say(f"  {q} original {O.rel} (unit {O.unit}, {O.unit_where}-table L{O.unit_line}): old-layout separate statement (table L{O.tab[0] + 1}), current-period column = {'누적' if q == '2023.2Q' else '분기'}")
        tol_by_q = 0.5 + 1e-6 if q == "2023.2Q" else 0.0051
        for item in sorted(oi):
            lv = LIVE.get((CODE, item, q))
            lvv = None if lv is None else lv["값"]
            if lvv is None:
                say(f"     i{item:>2}: live master blank, original {oi[item]:,.6f}")
                continue
            d = oi[item] - lvv
            ok = abs(d) <= tol_by_q
            tag = "reproduced" if ok else "differs"
            if not ok and item == 16 and q == "2023.2Q":
                tag = "differs (live item 16 = 5,400 comes from the 경영공시 PDF in 억원; the filing prints 5,349.343195 = the builder override 5,349)"
            say(f"     i{item:>2}: live {lvv:>16,.6f} original cumulative {oi[item]:>16,.6f} diff {d:+.6f} -> {tag}")
            if not ok and not (item == 16 and q == "2023.2Q"):
                ctrl_bad += 1
                problem(f"control {q} i{item}", f"live master does not reproduce the original filing ({oi[item]} vs {lvv})")
        # item 1 / 17 / 18 of the old layout (no 보험손익 row): live item 1 = item 2 (+ 15 - 16 for Q1)
        lv1, lv2 = LIVE[(CODE, 1, q)]["값"], LIVE[(CODE, 2, q)]["값"]
        expl = ("item 1 = original item 2 - original item 16 (rounded to 2 decimals), the standard definition" if q == "2023.1Q" and abs(lv1 - (oi[2] - oi[16])) <= 0.0051
                else ("item 1 = original item 2 (기타사업비용 NOT deducted: a different definition than 2023.1Q/3Q/4Q, where item 1 = item 2 - item 16; "
                      f"on the standard definition the live value would be {oi[2] - oi[16]:,.3f})" if q == "2023.2Q" and abs(lv1 - oi[2]) <= 0.5 + 1e-6 else "UNEXPLAINED"))
        say(f"     i 1: live {lv1:,.2f} | the original statement has no 보험손익 row; original item 2 {oi[2]:,.3f}, original item 16 {oi[16]:,.3f} -> {expl}")
        if expl == "UNEXPLAINED":
            ctrl_bad += 1
            problem(f"control {q} i1", "live item 1 is not explained by the original statement")
        if q == "2023.2Q":
            n3 = pl4_note(F["O2"], "cur")
            say(f"     i 4: live {LIVE[(CODE, 4, q)]['값']:,.1f} (owner gold) | original note (3) 제공된 서비스의 보험계약마진: 3개월 {n3['cur_3m']['printed']} (L{n3['cur_3m']['line']}) / 누적 {n3['cur_cum']['printed']} (L{n3['cur_cum']['line']}) -> the live value is the CUMULATIVE column (the pre-fix builder value 12,290 was the 3개월 column)")
            if abs(LIVE[(CODE, 4, q)]["값"] - n3["cur_cum"]["mn"]) > 0.5:
                ctrl_bad += 1
                problem("control 2023.2Q i4", "live item 4 is not the original cumulative column")
    # 2023.1Q PL4 and 5 of the original: item 4 live 11,125 = CSM roll-forward (11,125)
    o1 = o1_csm_cur(F["O1"])
    say(f"  2023.1Q original: PL4 live {LIVE[(CODE, 4, '2023.1Q')]['값']:,.0f} vs original CSM roll-forward row 서비스 제공으로 당기손익으로 인식된보험계약마진 {o1['rows'][5]['printed']} (L{o1['rows'][5]['line']}) -> "
        f"{'reproduced' if abs(LIVE[(CODE, 4, '2023.1Q')]['값'] + o1['rows'][5]['mn']) <= 0.5 else 'differs'}")
    if abs(LIVE[(CODE, 4, "2023.1Q")]["값"] + o1["rows"][5]["mn"]) > 0.5:
        ctrl_bad += 1
        problem("control 2023.1Q i4", "original CSM release does not reproduce live item 4")

    say("  CSM original current-period tables (separate notes) vs the live (pre-load) CSM master (억원):")
    ORIG_CSM = {"2023.1Q": o1}
    for q in ("2023.2Q", "2023.3Q", "2023.4Q"):
        ORIG_CSM[q] = csm_tables(F[OLDKEY[q]])["cur"]
    for q in QUARTERS:
        T = ORIG_CSM[q]
        for i in range(1, 7):
            r = T["rows"][i]
            lv = LIVEC[(CODE, i, q)]["값"]
            exact = r2(r["mn"] / 100.0)
            g = GOLDC.get((CODE, i, q))
            note = ""
            if g is not None:
                ok = abs(g["값"] - exact) <= MASK_TOL
                cls = "A (original print)" if ok else "B (not the original print)"
                note = f"[owner gold {g['값']}; builder value `was` {g.get('was')}; gold vs original print {g['값'] - exact:+.2f} -> class {cls}]"
                if (q, i) in APPROVED_CSM_GOLD_A and not ok:
                    ctrl_bad += 1
                    problem(f"control {q} CSM i{i}", f"approved class-A gold {g['값']} is not the original print {exact}")
                if (q, i) in APPROVED_CSM_GOLD_B:
                    ok_b = abs(g["값"] - exact) > MASK_TOL
                    if not ok_b:
                        problem(f"control {q} CSM i{i}", f"approved class-B gold {g['값']} equals the original print {exact}")
                ok = True
            else:
                tol = 0.0501
                ok = abs(lv - round(exact, 1)) <= tol
            say(f"     {q} CSM i{i}: live {lv:>9,.2f} original print {r['printed']:>9s} (L{r['line']}) = {exact:>9,.2f} -> {'consistent' if ok else 'DIFFERS'} {note}")
            if not ok:
                ctrl_bad += 1
                problem(f"control {q} CSM i{i}", "original print does not reproduce the live CSM master")
    RES["control_bad"] = ctrl_bad

    # ================================================================ E. plan sanity
    say("\n== E. plan sanity")
    n_gn, n_gr = len(contract["gold_new"]), len(contract["gold_replace"])
    n_cn, n_cr = len(contract["csm_gold_new"]), len(contract["csm_gold_replace"])
    n_crm = len(contract.get("csm_gold_remove", []))
    say(f"  contract: PL gold_new {n_gn} gold_replace {n_gr} | CSM gold_new {n_cn} gold_replace {n_cr} gold_remove {n_crm} | null_dangi_add {len(contract['null_dangi_add'])} set_dangi_add {len(contract['set_dangi_add'])} held {len(contract['held'])}")
    if n_gn + n_gr != len(plan_pl):
        problem("contract", f"PL contract {n_gn + n_gr} != planned PL cells {len(plan_pl)}")
    if n_cn + n_cr + n_crm != len(plan_csm):
        problem("contract", f"CSM contract {n_cn + n_cr + n_crm} != planned CSM cells {len(plan_csm)}")
    repl = {(e["quarter"], e["item"]) for e in contract["gold_replace"]}
    replc = {(e["quarter"], e["item"]) for e in contract["csm_gold_replace"]} | {(e["quarter"], e["item"]) for e in contract.get("csm_gold_remove", [])}
    if repl != APPROVED_PL_GOLD or replc != (APPROVED_CSM_GOLD_A | APPROVED_CSM_GOLD_B):
        problem("contract", f"replaced owner gold {sorted(repl)} / {sorted(replc)} != approved {sorted(APPROVED_PL_GOLD)} / {sorted(APPROVED_CSM_GOLD_A | APPROVED_CSM_GOLD_B)}")
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
    for (q, item) in sorted(repl):
        g = GOLD[(CODE, item, q)]
        if item == 4:
            n4o = pl4_note(F[OLDKEY[q]], "cur")
            say(f"  PL gold {q} i4: gold {g['값']} == original note cumulative {n4o['printed']} (L{n4o['line']}) of the separate notes of rcept {Path(F[OLDKEY[q]]).stem} (the 3개월 column prints {n4o['prior_3m']['printed'] if 'prior_3m' in n4o else '-'}) -> class A (original print); latest print {NEW[q]['n4']['printed']} (L{NEW[q]['n4']['line']})")
            if abs(g["값"] - n4o["mn"]) > 1e-9:
                problem(f"{q} i4", "gold is not the original print")
        else:
            l3, l4, l5, l6 = (LIVE[(CODE, j, q)]["값"] for j in (3, 4, 5, 6))
            formula = l3 - (l4 + l5 + l6)
            live7 = LIVE[(CODE, 7, q)]["값"]
            say(f"  PL gold {q} i7: derived plug 3-(4+5+6): gold {g['값']} | formula from the live legs {formula:,.6f} | live master {live7:,.6f} -> "
                + ("the live master cell equals the formula (hand-corrected after the 2026-10-11 A2 leg fix); the gold entry is stale" if abs(live7 - formula) <= 1e-6 and abs(g['값'] - formula) > 1e-6 else "gold = formula"))
    for (q, item) in sorted(replc):
        g = GOLDC[(CODE, item, q)]
        o = r2(ORIG_CSM[q]["rows"][item]["mn"] / 100.0)
        n = r2(CSMN[q]["rows"][item]["mn"] / 100.0)
        was = g.get("was")
        cls = "B (chain-forced: neither the original print nor the latest comparative)" if (abs(g["값"] - o) > MASK_TOL and abs(g["값"] - n) > MASK_TOL) else "A (original print)"
        say(f"  CSM gold {q} i{item}: gold {g['값']} (builder value `was` {was}) | original print {o} | latest comparative {n} -> class {cls}")
        if (q, item) in APPROVED_CSM_GOLD_B and not cls.startswith("B"):
            problem(f"{q} CSM i{item}", "gold class is not B")
        if (q, item) in APPROVED_CSM_GOLD_A and not cls.startswith("A"):
            problem(f"{q} CSM i{item}", "gold class is not A")
    # mask test for the CSM cells against the builder diag
    for (q, i), c in sorted(plan_csm.items()):
        sv = src_csm.get((CODE, i, q), {}).get("값")
        if sv is not None and abs(c["new"] - sv) <= MASK_TOL:
            say(f"  CSM {q} i{i}: planned {c['new']} is within {MASK_TOL} of the builder diag value {sv} -> a gold entry would be MASKED"
                + (" (approved chain-forced entry: REMOVED instead of replaced)" if (q, i) in APPROVED_CSM_GOLD_B else " -> PROBLEM"))
            if (q, i) not in APPROVED_CSM_GOLD_B:
                problem(f"{q} CSM i{i}", "planned CSM cell would be a masked gold cell")

    ok_all = not PROBLEMS
    say(f"\nRESULT: {'ALL OK' if ok_all else str(len(PROBLEMS)) + ' PROBLEM(S)'} | PL cells {RES['pl_cells_ok']}/{RES['pl_cells']} | CSM cells {RES['csm_cells_ok']}/{RES['csm_cells']} | control problems {RES['control_bad']}")
    tag = f"_{OUTTAG}" if OUTTAG else ""
    if not MUTATE:
        vals = dict(
            pl={q: {str(i): round(v, 6) for i, v in NEW[q]["items"].items()} for q in QUARTERS},
            csm_exact={q: [r2(CSMN[q]["rows"][i + 1]["mn"] / 100.0) for i in range(6)] for q in QUARTERS},
            printed_3m={q: {str(i): round(v, 6) for i, v in items_from(NEW[q]["S"].read(2023, "3m")).items()} for q in ("2023.2Q", "2023.3Q")},
            seams={f"{q}|{i}": v[1] for (q, i), v in seam_mine.items()})
        (HERE / "kr0072_verify_values.json").write_text(json.dumps(vals, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    (HERE / f"kr0072_verify{tag}.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8", newline="\n")
    (HERE / f"kr0072_verify{tag}.json").write_text(json.dumps(dict(problems=PROBLEMS, res=RES, mutate=MUTATE, ok=ok_all), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
