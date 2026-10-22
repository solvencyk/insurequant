# -*- coding: utf-8 -*-
"""KR0032 (NH Nonghyup Non-life) latest-comparative adoption plan -- READ-ONLY on every master / gold / doc.
Independent re-read of the SEPARATE-basis statement of comprehensive income ("4-2. 포괄손익계산서") of the next-year filing (prior cumulative column),
of the original filing (to prove master = original print) and of the restatement-note tables (수정 전 / 수정금액 / 수정 후) as a third source;
closure on the merged vector (gate identities), single-quarter (값_당분기) seam analysis.
Writes plan_KR0032.json + KR0032_plan_report.txt next to this script.  python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import KR0032_xml as X
import KR0032_s1_note as NT
ROOT = X.ROOT
sys.stdout.reconfigure(encoding="utf-8")
CODE, NAME = "KR0032", "NH농협손해보험"
TOL_WON = 2e-5          # won-precision print vs master (6 decimals of 백만원)
TOL_RND = 1.0           # million-won rounded print (restatement note)

ITEM_NAME = {1: "보험손익", 2: "생명장기 손익", 13: "자동차손익", 14: "일반손익", 15: "기타영업수익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익",
             20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익",
             27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익", 30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CHECK_ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

RCEPT = {"FY2023_Q1": "20230515002460", "FY2023_Q2": "20230814001056", "FY2023_Q3": "20231114000995", "FY2023_Q4": "20240329001662",
         "FY2024_Q1": "20240514001436", "FY2024_Q2": "20240814001448", "FY2024_Q3": "20241114001354", "FY2024_Q4": "20250331003247",
         "FY2025_Q1": "20250515001078", "FY2025_Q2": "20250814001701", "FY2025_Q3": "20251114001790", "FY2025_Q4": "20260331004099"}
# orig  = (filing, column of the CURRENT-period cumulative value)    (master was built from this)
# later = (filing, column of the PRIOR-period cumulative value, column of the prior-period 3-month value)
SPEC = {
    "2023.4Q": dict(orig=("FY2023_Q4", ("pos", 0)), later=("FY2024_Q4", ("ctx", "PFY2023dFY"), None), note="FY2024_Q4", third=("FY2025_Q4", ("ctx", "BPFY2023dFY"))),
    "2024.1Q": dict(orig=("FY2024_Q1", ("pos", 1)), later=("FY2025_Q1", ("ctx", "PFY2024dFQA"), ("ctx", "PFY2024dFQQ")), note="FY2025_Q1", third=None),
    "2024.2Q": dict(orig=("FY2024_Q2", ("pos", 1)), later=("FY2025_Q2", ("ctx", "PFY2024dHYA"), ("ctx", "PFY2024dHYQ")), note="FY2025_Q2", third=None),
    "2024.3Q": dict(orig=("FY2024_Q3", ("pos", 1)), later=("FY2025_Q3", ("ctx", "PFY2024dTQA"), ("ctx", "PFY2024dTQQ")), note="FY2025_Q3", third=None),
}
# vintage (accounting-policy generation) of every YTD cell AFTER the adoption.  new = systematic-allocation change applied (FY2024 annual report onward);
# old = the print of the FY2023 filings and of the FY2024 Q1..Q3 reports (their 2023 comparative columns were NOT restated -- proven in verification.fy2023_*).
VINT_AFTER = {"2023.1Q": "old", "2023.2Q": "old", "2023.3Q": "old", "2023.4Q": "new", "2024.1Q": "new", "2024.2Q": "new", "2024.3Q": "new", "2024.4Q": "new"}

HAS_LETTER = re.compile(r"[가-힣A-Za-z]")
RE_ROMAN = re.compile(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫIVXLC]+\.")
RE_NUMB = re.compile(r"^(\d+\)|\d+\.|\(\d+\))")


def norm(label):
    s = (label or "").replace("\u3000", "").replace(" ", "")
    s = RE_ROMAN.sub("", s)
    s = RE_NUMB.sub("", s)
    s = s.replace("(손실)", "")
    return s


def unit_of(rows):
    for r in rows[:12]:
        t = r["label"][0] if r["label"] else ""
        if "단위" in t:
            return "백만원" if "백만원" in t else ("원" if "원" in t else "?")
    return "?"


class Stmt:
    def __init__(self, fy):
        self.fy = fy
        self.title, self.end, self.rows = X.read_statement(fy)
        self.unit = unit_of(self.rows)
        self.rel = X.FILES[fy]
        self.idx = defaultdict(list)
        for r in self.rows:
            self.idx[norm(r["label"][0] if r["label"] else "")].append(r)

    def header(self):
        out = {}
        for r in self.rows:
            lab = (r["label"][0] if r["label"] else "")
            if lab == "3개월":
                out["col_header_row"] = dict(tr_line=r["tr_line"], texts=["3개월"] + [c["text"] for c in r["cells"]], lines=[r["label"][1]] + [c["line"] for c in r["cells"]])
            if lab == "" and r["cells"] and r["cells"][0]["text"].startswith("제 "):
                out["period_header_row"] = dict(tr_line=r["tr_line"], texts=[c["text"] for c in r["cells"]], lines=[c["line"] for c in r["cells"]])
        return out

    def ctxs(self):
        return sorted({X.short_ctx(c["ctx"]) for r in self.rows for c in r["cells"] if c["ctx"]})

    def pick(self, names, col):
        for n in names:
            rs = self.idx.get(n)
            if not rs:
                continue
            if len(rs) != 1:
                raise RuntimeError(f"{self.fy}: ambiguous label {n}: {len(rs)} rows")
            r = rs[0]
            if col[0] == "pos":
                c = r["cells"][col[1]]
            else:
                cs = [c for c in r["cells"] if c["ctx"].startswith(col[1] + "_") and "SeparateMember" in c["ctx"]]
                if len(cs) != 1:
                    raise RuntimeError(f"{self.fy}: {n} ctx {col[1]}: {len(cs)} cells")
                c = cs[0]
            if c["val"] is None:
                raise RuntimeError(f"{self.fy}: {n} {col}: empty cell L{c['line']}")
            scale = 1e6 if self.unit == "원" else 1.0
            return dict(val=c["val"] / scale, raw=c["text"], line=c["line"], label=r["label"][0])
        raise KeyError(f"{self.fy}: none of {names}")


ITEM_LABELS = {
    1: ["보험손익"], 16: ["기타사업비용"], 17: ["투자손익"], 20: ["영업이익"], 22: ["법인세차감전순이익"], 23: ["법인세비용"],
    24: ["당기순이익", "분기순이익", "반기순이익"], 25: ["기타포괄손익"], 26: ["기타포괄손익-공정가치측정금융자산관련손익"], 27: ["보험금융순손익"],
    28: ["현금흐름위험회피파생상품평가손익"], 29: ["기타포괄손익-공정가치측정유가증권평가손익"], 30: ["재보험금융순손익"], 31: ["총포괄손익", "총포괄이익", "총포괄손실"],
    32: ["확정급여제도의재측정요소"],
}


def P(p, sign):
    return dict(label=p["label"], line=p["line"], raw=p["raw"], sign=sign)


def read_items(st, col):
    out = {}
    for it, names in ITEM_LABELS.items():
        p = st.pick(names, col)
        out[it] = dict(val=p["val"], parts=[P(p, 1)])
    a = st.pick(["보험금융수익"], col)
    b = st.pick(["재보험금융수익"], col)
    c = st.pick(["보험금융비용"], col)
    d = st.pick(["재보험금융비용"], col)
    out[19] = dict(val=a["val"] + b["val"] - c["val"] - d["val"], parts=[P(a, 1), P(b, 1), P(c, -1), P(d, -1)])
    a = st.pick(["영업외수익"], col)
    b = st.pick(["영업외비용"], col)
    out[21] = dict(val=a["val"] - b["val"], parts=[P(a, 1), P(b, -1)])
    out[18] = dict(val=out[17]["val"] - out[19]["val"], parts=[dict(label="derived 17-19", line=None, raw=None, sign=0)])
    return out


# ------------------------------------------------------------------ masters (read only)
def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


pl_rows = load_json("PL_breakdown.json")
M = defaultdict(dict)
for r in pl_rows:
    if r["원보험사코드"] == CODE:
        M[r["항목번호"]][r["공시분기"]] = r
gold = load_json("data/_gold/user_pl_cells.json")
GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"] if e["원보험사코드"] == CODE}
NULL_D = sorted(tuple(x) for x in gold.get("null_dangi", {}).get("cells", []) if x[0] == CODE)
SET_D = sorted(tuple(x[:3]) for x in gold.get("set_dangi", {}).get("cells", []) if x[0] == CODE)
d5 = {(b["code"], b["q"]): b for b in load_json("data/_derived/remaining_20261022/d_census/d5_buckets.json")}


def mval(item, q):
    r = M.get(item, {}).get(q)
    return None if r is None else r["값"]


def mdangi(item, q):
    r = M.get(item, {}).get(q)
    return None if r is None else r.get("값_당분기")


ST = {}


def stmt(fy):
    if fy not in ST:
        ST[fy] = Stmt(fy)
    return ST[fy]


warnings = []
ORIG_VAL, LATER_VAL, LATER_3M, THIRD_VAL = {}, {}, {}, {}
for q, sp in SPEC.items():
    ofy, ocol = sp["orig"]
    lfy, lcol, l3 = sp["later"]
    ORIG_VAL[q] = read_items(stmt(ofy), ocol)
    LATER_VAL[q] = read_items(stmt(lfy), lcol)
    if l3 is not None:
        LATER_3M[q] = read_items(stmt(lfy), l3)
    if sp["third"]:
        THIRD_VAL[q] = read_items(stmt(sp["third"][0]), sp["third"][1])

# ------------------------------------------------------------------ restatement-note tables (third source)
NOTE = {}
for fy in NT.NOTE_START:
    s, stop, rows = NT.read_note(fy)
    tab = {}
    for r in rows:
        if len(r) == 4:
            lab = norm(r[0][0])
            vals = [(NT.num(t), ln) for t, ln in r[1:]]
            tab[lab] = dict(label=r[0][0], label_line=r[0][1], before=vals[0], adj=vals[1], after=vals[2])
    NOTE[fy] = dict(start=s, end=stop, rows=tab)
NOTE_LABEL = {17: "투자손익", 20: "영업이익", 22: "법인세비용차감전순이익", 23: "법인세비용", 24: None, 25: "기타포괄손익", 1: "보험손익", 31: None}


def note_cell(fy, item):
    tab = NOTE[fy]["rows"]
    keys = {17: ["투자손익"], 20: ["영업이익"], 22: ["법인세비용차감전순이익"], 23: ["법인세비용"], 24: ["당기순이익", "분기순이익", "반기순이익"], 25: ["기타포괄손익"],
            1: ["보험손익"], 31: ["총포괄이익", "총포괄손실", "총포괄손익"]}.get(item)
    if not keys:
        return None
    for k in keys:
        if k in tab:
            return tab[k]
    return None


# ------------------------------------------------------------------ changed items per bucket
changed = {}
for q, sp in SPEC.items():
    ch = []
    for it in CHECK_ITEMS:
        old = mval(it, q)
        if old is None:
            warnings.append(f"{q} item {it}: master empty")
            continue
        org = ORIG_VAL[q][it]["val"]
        if abs(old - org) > TOL_WON:
            warnings.append(f"{q} item {it}: master {old} != original print {org}")
        if abs(LATER_VAL[q][it]["val"] - old) > TOL_WON:
            ch.append(it)
    changed[q] = ch

cells = []
for q, sp in SPEC.items():
    lfy, lcol, l3 = sp["later"]
    sl = stmt(lfy)
    cen = d5[(CODE, q)]["its"]
    for it in changed[q]:
        lat = LATER_VAL[q][it]
        old = mval(it, q)
        cn = cen[str(it)]
        nc = note_cell(sp["note"], it)
        note = None
        if nc is not None:
            note = dict(kind="restatement note table (수정 전 / 수정금액 / 수정 후), rounded to million won", file=stmt(sp["note"]).rel,
                        label=nc["label"], line_after=nc["after"][1], line_before=nc["before"][1], after=nc["after"][0], before=nc["before"][0], adj=nc["adj"][0],
                        after_vs_xml_diff=round(nc["after"][0] - lat["val"], 6), before_vs_master_diff=round(nc["before"][0] - old, 6),
                        ok_after=abs(nc["after"][0] - lat["val"]) <= TOL_RND, ok_before=abs(nc["before"][0] - old) <= TOL_RND)
        third = None
        if q in THIRD_VAL:
            tv = THIRD_VAL[q][it]
            third = dict(kind="FY2025 annual report, separate statement, FY2023 column (BPFY2023dFY)", file=stmt(sp["third"][0]).rel, line=tv["parts"][0]["line"],
                         value=round(tv["val"], 6), diff_vs_xml=round(tv["val"] - lat["val"], 6), ok=abs(tv["val"] - lat["val"]) <= TOL_WON)
        cells.append(dict(
            quarter=q, item=it, item_name=ITEM_NAME[it], old=old, new=round(lat["val"], 6), delta=round(lat["val"] - old, 6),
            unit="백만원", source_unit=sl.unit, source_print="won (exact)",
            xml_file=sl.rel, xml_rcept=RCEPT[lfy], xml_period_column=f"{lcol[1]} (separate/OFS statement, prior-period cumulative)",
            xml_line=lat["parts"][0]["line"],
            xml_lines=[dict(label=p["label"], line=p["line"], printed=p["raw"], sign=p["sign"]) for p in lat["parts"]],
            derivation=("direct print" if len(lat["parts"]) == 1 and lat["parts"][0]["sign"] == 1 else "sum of printed lines (signs in xml_lines)"),
            second_source=dict(kind="FS-API frmtrm column of the same filing (census d5_buckets.json)", value=cn["prior"], diff_vs_xml=round(cn["prior"] - lat["val"], 6)),
            note_table_source=note, third_xml_source=third,
            census_new=cn["prior"], census_master=cn["master"],
            master_equals_original_print=abs(old - ORIG_VAL[q][it]["val"]) <= TOL_WON,
            original_print=dict(value=round(ORIG_VAL[q][it]["val"], 6), xml_file=stmt(sp["orig"][0]).rel, xml_line=ORIG_VAL[q][it]["parts"][0]["line"]),
            gold_cell=((CODE, it, q) in GOLD)))

for c in cells:
    lf = SPEC[c["quarter"]]["later"]
    c["gold_note"] = (f"2026-10-22 parser/ifrs17 (KR0032 최신 비교열 채택, owner 결정 2026-10-22, 교보생명 선례와 동일): 별도(OFS) 기준 누계. {lf[0]} rcept {RCEPT[lf[0]]} 의 "
                      f"전기 누적 열({lf[1][1]}) = 재작성 값. 원문 {c['xml_file']} L{c['xml_line']}" + ("" if c["derivation"] == "direct print" else " 외 합산 줄(xml_lines)") +
                      f". 단위 원(정밀). 2차 근거 FS-API frmtrm 일치" + ("; 재작성 주석 표 수정 후 일치" if c["note_table_source"] else "") +
                      ". 재작성 사유: 금리연동형 보험계약 보험금융손익 체계적배분 변경(당기순이익 -> 기타포괄손익). 증거 data/_derived/remaining_20261022/e19_latest_comparative/plan_KR0032.json")


# ------------------------------------------------------------------ closure on the merged vector
def merged_vec(q, adopted=True):
    v = {it: mval(it, q) for it in range(1, 33)}
    if adopted:
        for c in cells:
            if c["quarter"] == q:
                v[c["item"]] = c["new"]
    return v


def tol_gate(lhs, floor):
    return max(0.001 * abs(lhs), floor)


def closure(q, adopted):
    v = merged_vec(q, adopted)
    res = []

    def chk(name, lhs, rhs, floor=200.0):
        if lhs is None or rhs is None:
            res.append(dict(name=name, status="SKIP (operand empty)"))
            return
        d = lhs - rhs
        res.append(dict(name=name, lhs=round(lhs, 6), rhs=round(rhs, 6), resid=round(d, 6), tol_strict=0.002, ok=abs(d) <= 0.002,
                        tol_gate=round(tol_gate(lhs, floor), 3), ok_gate=abs(d) <= tol_gate(lhs, floor)))

    chk("G1 17 = 18 + 19", v[17], v[18] + v[19])
    chk("G2 20 = 1 + 17", v[20], v[1] + v[17], 600.0)
    chk("G3 22 = 20 + 21", v[22], v[20] + v[21])
    chk("G4 24 = 22 - 23", v[24], v[22] - v[23])
    chk("G5 |22-24| = |23|", abs(v[22] - v[24]), abs(v[23]))
    chk("G6 31 = 24 + 25", v[31], v[24] + v[25])
    oci = [26, 27, 28, 29, 30, 32]
    chk("G7 25 = 26+27+28+29+30+32", v[25], sum(v[i] for i in oci) if all(v[i] is not None for i in oci) else None)
    bare = sum(x for x in (v[2], v[13], v[14]) if x is not None)
    cand = [bare]
    if v[15] is not None and v[16] is not None:
        cand.append(bare + v[15] - v[16])
    d = min((c - v[1] for c in cand), key=abs)
    res.append(dict(name="G8 LOB bridge 1 = 2+13+14 (+15-16)", lhs=round(v[1], 6), rhs=round(v[1] + d, 6), resid=round(d, 6), tol_strict=0.002, ok=abs(d) <= 0.002,
                    tol_gate=round(tol_gate(v[1], 200.0), 3), ok_gate=abs(d) <= tol_gate(v[1], 200.0),
                    note="legs 2=%s 13=%s 14=%s 15=%s 16=%s (master Tier-2 legs, untouched)" % (v[2], v[13], v[14], v[15], v[16])))
    return res


def printed_closure(q):
    L = LATER_VAL[q]
    out = []

    def chk(n, a, b):
        out.append(dict(name=n, resid=round(a - b, 6), tol_strict=0.002, ok=abs(a - b) <= 0.002))

    chk("printed 20 = printed 1 + printed 17", L[20]["val"], L[1]["val"] + L[17]["val"])
    chk("printed 22 = printed 20 + printed 21 (nonop income - expense)", L[22]["val"], L[20]["val"] + L[21]["val"])
    chk("printed 24 = printed 22 - printed 23", L[24]["val"], L[22]["val"] - L[23]["val"])
    chk("printed 31 = printed 24 + printed 25", L[31]["val"], L[24]["val"] + L[25]["val"])
    chk("printed 25 = 26+27+28+29+30+32 (leaf rows)", L[25]["val"], sum(L[i]["val"] for i in (26, 27, 28, 29, 30, 32)))
    return out


gold_overlap = {q: [it for it in changed[q] if (CODE, it, q) in GOLD] for q in SPEC}
gold_in_block = {q: sorted(it for (c, it, qq) in GOLD if qq == q) for q in SPEC}
buckets = []
for q in SPEC:
    ids_before, ids_after, pc = closure(q, False), closure(q, True), printed_closure(q)
    core_ok = all(x.get("ok", True) for x in ids_after if not x["name"].startswith("G8")) and all(x["ok"] for x in pc)
    g8b = [x for x in ids_before if x["name"].startswith("G8")][0]
    g8a = [x for x in ids_after if x["name"].startswith("G8")][0]
    # the LOB bridge carries a small pre-existing residual (Tier-2 legs are rounded in the master): it must be UNCHANGED by the adoption (item 1 and the legs are not touched) and inside the gate tolerance
    bridge_ok = abs(g8a["resid"] - g8b["resid"]) < 1e-9 and g8a["ok_gate"]
    ok_after = core_ok and bridge_ok
    sp = SPEC[q]
    census_items = sorted(int(k) for k, v in d5[(CODE, q)]["its"].items() if abs(v["prior"] - v["master"]) > 1e-3)
    note_ok = all((c["note_table_source"]["ok_after"] and c["note_table_source"]["ok_before"]) for c in cells if c["quarter"] == q and c["note_table_source"])
    adopt = bool(ok_after and not gold_overlap[q])
    buckets.append(dict(
        quarter=q, adopt=adopt, n_cells=len(changed[q]), items=changed[q],
        original_filing=dict(fy=sp["orig"][0], rcept=RCEPT[sp["orig"][0]], file=stmt(sp["orig"][0]).rel, statement_title_line=stmt(sp["orig"][0]).title,
                             unit=stmt(sp["orig"][0]).unit, column=str(sp["orig"][1])),
        later_filing=dict(fy=sp["later"][0], rcept=RCEPT[sp["later"][0]], file=stmt(sp["later"][0]).rel, statement_title_line=stmt(sp["later"][0]).title,
                          unit=stmt(sp["later"][0]).unit, column=sp["later"][1][1], three_month_column=(sp["later"][2][1] if sp["later"][2] else None),
                          restatement_note=dict(fy=sp["note"], file=stmt(sp["note"]).rel, table_first_line=NOTE[sp["note"]]["start"], all_checked_cells_ok=note_ok)),
        census_items=census_items, items_equal_to_census=(census_items == changed[q]),
        gold_cells_in_block=gold_in_block[q], gold_overlap_with_adopted_items=gold_overlap[q],
        closure_master_before=ids_before, closure_merged_after=ids_after, closure_printed_later_filing=pc,
        csm_vs_master=d5[(CODE, q)]["csm"]["status"],
        lob_bridge=dict(resid_before=g8b["resid"], resid_after=g8a["resid"], unchanged_by_adoption=abs(g8a["resid"] - g8b["resid"]) < 1e-9, within_gate_tolerance=g8a["ok_gate"], gate_tolerance=g8a["tol_gate"]),
        reason=("closes on the merged vector (G1-G7 strict 0.002 million won; G8 LOB bridge residual %.6f is pre-existing, identical before/after, far inside the gate tolerance %.1f); "
                "no owner gold cell in the block; CSM latest = master (census SAME)" % (g8a["resid"], g8a["tol_gate"])
                if adopt else "NOT CLOSED or gold overlap -- see closure lists")))


# ------------------------------------------------------------------ single quarter analysis
def derived(ytd, q):
    cur = ytd.get(q)
    if cur is None:
        return None
    n = int(q[5])
    y = q[:4]
    if n == 1:
        return cur
    prev = ytd.get(f"{y}.{n-1}Q")
    return None if prev is None else round(cur - prev, 6)


adopted_new = {(c["item"], c["quarter"]): c["new"] for c in cells}
POLICY_ITEMS = sorted({c["item"] for c in cells})
model_mismatch, seam_cells, neighbour_effects, auto_follow = [], [], [], []
for item in POLICY_ITEMS:
    for fy in ("2023", "2024"):
        qs = [f"{fy}.{n}Q" for n in (1, 2, 3, 4)]
        ytd_b = {q: mval(item, q) for q in qs}
        ytd_a = {q: adopted_new.get((item, q), mval(item, q)) for q in qs}
        for q in qs:
            db_model, db_live, da = derived(ytd_b, q), mdangi(item, q), derived(ytd_a, q)
            if (db_model is None) != (db_live is None) or (db_model is not None and abs(db_model - db_live) > 1e-5):
                model_mismatch.append((item, q, db_model, db_live))
            n = int(q[5])
            cur_changed = (item, q) in adopted_new
            prev_changed = n > 1 and (item, f"{fy}.{n-1}Q") in adopted_new
            if not cur_changed and not prev_changed:
                continue
            if n == 1:
                auto_follow.append(dict(quarter=q, item=item, old=db_live, derived_after=da, why="Q1 single quarter = YTD of the same bucket (also printed as 3-month column)"))
                continue
            pq = f"{fy}.{n-1}Q"
            rec = dict(quarter=q, item=item, item_name=ITEM_NAME[item], old=db_live, derived_after_adoption=da,
                       operand_cur=dict(q=q, ytd_before=ytd_b[q], ytd_after=ytd_a[q], vintage_after=VINT_AFTER[q], adopted=cur_changed),
                       operand_prev=dict(q=pq, ytd_before=ytd_b[pq], ytd_after=ytd_a[pq], vintage_after=VINT_AFTER[pq], adopted=prev_changed))
            if da is None:
                rec["class"] = "no_derived_cell"
                neighbour_effects.append(rec)
                continue
            if VINT_AFTER[q] != VINT_AFTER[pq]:
                rec["class"] = "seam"
                rec["proposed"] = "null_dangi"
                rec["printed_three_month_column_in_later_filing"] = False
                rec["three_month_check_filing"] = dict(file=stmt(SPEC[q]["later"][0]).rel if q in SPEC else None,
                                                       statement_contexts=stmt(SPEC[q]["later"][0]).ctxs() if q in SPEC else None)
                rec["reason"] = ("YTD of this quarter is the restated comparative of the FY2024 annual report (systematic-allocation change); the previous-quarter YTD stays the original "
                                 "FY2023 Q3 print because no restated 9M-2023 exists: the FY2024 Q3 report still prints the pre-change 9M-2023 column (master == that print, "
                                 "verification.fy2023_ytd_master_vs_fy2024_filings_prior). The annual report prints no 3-month Q4 column (contexts: current FY, prior FY, FY-2 only), "
                                 "so no set_dangi value exists -> blank (owner rule 2026-10-22; precedent KR0073 / KR0087)")
                seam_cells.append(rec)
            elif cur_changed and prev_changed:
                rec["class"] = "both_adopted"
                auto_follow.append(rec)
            elif (not cur_changed) and prev_changed:
                rec["class"] = "consistent_after_adoption"
                neighbour_effects.append(rec)
            else:
                rec["class"] = "other"
                neighbour_effects.append(rec)

# 3-month check against the printed prior-period 3-month column
dangi_vs_printed = []
for q in ("2024.1Q", "2024.2Q", "2024.3Q"):
    fy = q[:4]
    pq = f"{fy}.{int(q[5])-1}Q"
    for item in POLICY_ITEMS:
        if (item, q) not in adopted_new:
            continue
        if q == "2024.1Q":
            da = adopted_new[(item, q)]
        elif (item, pq) in adopted_new:
            da = round(adopted_new[(item, q)] - adopted_new[(item, pq)], 6)
        else:
            continue
        p3 = LATER_3M[q][item]
        dangi_vs_printed.append(dict(quarter=q, item=item, derived=da, printed_3m=round(p3["val"], 6), diff=round(da - p3["val"], 6), xml_line=p3["parts"][0]["line"],
                                     xml_file=stmt(SPEC[q]["later"][0]).rel, ok=abs(da - p3["val"]) <= 2e-5))

# 2024.4Q: YTD (new method already) vs the FY2025 annual's prior column, and the single-quarter before/after
s24, s25 = stmt("FY2024_Q4"), stmt("FY2025_Q4")
cur24 = read_items(s24, ("ctx", "CFY2024dFY"))
pri25 = read_items(s25, ("ctx", "PFY2024dFY"))
fy24 = []
for it in sorted(set(POLICY_ITEMS) | set(CHECK_ITEMS)):
    m = mval(it, "2024.4Q")
    fy24.append(dict(quarter="2024.4Q", item=it, master=m, fy2024_annual_current=round(cur24[it]["val"], 6), fy2025_annual_prior=round(pri25[it]["val"], 6),
                     equal_current=(m is not None and abs(m - cur24[it]["val"]) <= TOL_WON), equal_prior=(m is not None and abs(m - pri25[it]["val"]) <= TOL_WON),
                     xml_line_current=cur24[it]["parts"][0]["line"], xml_line_prior=pri25[it]["parts"][0]["line"]))

# FY2023 YTD of the old-vintage quarters vs the FY2024 filings' prior-period cumulative column (proves no restated 9M/6M/3M-2023 exists)
fy23 = []
for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):
    st = stmt(fy)
    vals = read_items(st, ("pos", 3))
    for it in CHECK_ITEMS:
        m = mval(it, q)
        rec = dict(quarter=q, item=it, later_print=round(vals[it]["val"], 6), xml_line=vals[it]["parts"][0]["line"], xml_file=st.rel, filing=fy, master=m)
        if m is not None:
            rec["diff"] = round(m - vals[it]["val"], 6)
            rec["equal_won"] = abs(m - vals[it]["val"]) <= TOL_WON
            rec["equal_rounded"] = abs(m - vals[it]["val"]) <= TOL_RND
        fy23.append(rec)
fy23_summary = {}
for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    rs = [r for r in fy23 if r["quarter"] == q and r["master"] is not None]
    fy23_summary[q] = dict(n_master_cells=len(rs), n_equal_won=sum(1 for r in rs if r["equal_won"]), n_equal_rounded=sum(1 for r in rs if r["equal_rounded"]),
                           unequal_items=[r["item"] for r in rs if not r["equal_rounded"]], empty_master_items=[r["item"] for r in fy23 if r["quarter"] == q and r["master"] is None])
# master 2023.3Q equals the FY2023 Q3 filing's own current-period print? (same as the line above but from the original filing)
orig23_3q = read_items(stmt("FY2023_Q3"), ("pos", 1))
orig23 = [dict(item=it, master=mval(it, "2023.3Q"), orig_print=round(orig23_3q[it]["val"], 6), xml_line=orig23_3q[it]["parts"][0]["line"],
               equal=(mval(it, "2023.3Q") is not None and abs(mval(it, "2023.3Q") - orig23_3q[it]["val"]) <= TOL_WON)) for it in CHECK_ITEMS]

# neighbour: 2023.1Q (not in the approved list)
nb_2023_1q = [dict(item=r["item"], master=r["master"], fy2024_q1_prior=r["later_print"], diff=r.get("diff"), xml_line=r["xml_line"]) for r in fy23
              if r["quarter"] == "2023.1Q" and r["master"] is not None and not r["equal_rounded"]]

# existing single-quarter of every other tier-1 item in the adopted buckets: unchanged (YTD unchanged) -> nothing to do
verification = dict(
    master_equals_original_print_all=all(abs(mval(it, q) - ORIG_VAL[q][it]["val"]) <= TOL_WON for q in SPEC for it in CHECK_ITEMS if mval(it, q) is not None),
    n_master_vs_original_cells=sum(1 for q in SPEC for it in CHECK_ITEMS if mval(it, q) is not None),
    warnings=warnings, dangi_model_mismatch_vs_live_master=model_mismatch,
    statements=dict((fy, dict(file=stmt(fy).rel, title_line=stmt(fy).title, end_line=stmt(fy).end, unit=stmt(fy).unit, contexts=stmt(fy).ctxs(), **stmt(fy).header()))
                    for fy in sorted({SPEC[q]["orig"][0] for q in SPEC} | {SPEC[q]["later"][0] for q in SPEC} | {"FY2024_Q4", "FY2025_Q4", "FY2023_Q3", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3"})),
    census_vs_xml=dict(n_cells=len(cells), max_abs_diff=max(abs(c["second_source"]["diff_vs_xml"]) for c in cells), items_equal_to_census_all_buckets=all(b["items_equal_to_census"] for b in buckets)),
    note_table_vs_xml=dict(n=sum(1 for c in cells if c["note_table_source"]), n_ok=sum(1 for c in cells if c["note_table_source"] and c["note_table_source"]["ok_after"] and c["note_table_source"]["ok_before"]),
                           items_not_in_note=sorted({c["item"] for c in cells if not c["note_table_source"]})),
    third_xml_source=dict(n=sum(1 for c in cells if c["third_xml_source"]), n_ok=sum(1 for c in cells if c["third_xml_source"] and c["third_xml_source"]["ok"])),
    gold=dict(KR0032_gold_set_cells=len(GOLD), adopted_cells_hitting_gold=[(c["quarter"], c["item"]) for c in cells if c["gold_cell"]],
              null_dangi_existing=NULL_D, set_dangi_existing=SET_D),
    printed_three_month_check=dict(n=len(dangi_vs_printed), n_ok=sum(1 for x in dangi_vs_printed if x["ok"]),
                                   max_abs_diff=max(abs(x["diff"]) for x in dangi_vs_printed) if dangi_vs_printed else None, rows=dangi_vs_printed),
    q2024_4Q_master_vs_fy2024_current_and_fy2025_prior=dict(rows=fy24, items_equal_both=[x["item"] for x in fy24 if x["equal_current"] and x["equal_prior"]],
                                                            items_not_equal=[x["item"] for x in fy24 if not (x["equal_current"] and x["equal_prior"])]),
    fy2023_ytd_master_vs_fy2024_filings_prior=dict(summary=fy23_summary, rows=fy23),
    fy2023_q3_master_vs_original_print=dict(n=len(orig23), n_equal=sum(1 for x in orig23 if x["equal"]), rows=orig23),
    neighbour_2023_1Q_outside_approved_list=dict(note="master 2023.1Q was loaded from the disclosure (rounded); the FY2024 Q1 report prints a different 2023.1Q comparative on these items "
                                                     "(a reclassification, not a policy PL<->OCI move). Not part of the 19 buckets; left unchanged.", rows=nb_2023_1q))
plan = dict(code=CODE, company=NAME, generated="2026-10-22", source_tool="data/_derived/remaining_20261022/e19_latest_comparative/KR0032_plan.py", master_unit="백만원",
            statement="separate (OFS) 4-2. 포괄손익계산서, prior-period cumulative column of the next-year filing", buckets=buckets, cells=cells,
            seam_cells=seam_cells, neighbour_effects=neighbour_effects, auto_follow_cells=auto_follow, verification=verification)
q24 = verification["q2024_4Q_master_vs_fy2024_current_and_fy2025_prior"]
plan["neighbours_outside_approved_list"] = {
    "2024.4Q": dict(ytd_status="unchanged: master equals the FY2024 annual current column and the FY2025 annual prior column on all %d checked items (new method already)" % len(q24["items_equal_both"]),
                    single_quarter="8 derived cells (items %s) change: 4Q YTD (new method) minus 9M YTD, which is old method today and new method after the 2024.3Q adoption -> consistent (neighbour_effects)" % ",".join(str(i) for i in POLICY_ITEMS)),
    "2023.3Q": dict(ytd_status="unchanged, old method: master equals the FY2023 Q3 own print (18/18) and the FY2024 Q3 report's prior 9M column (18/18) -> no restated 9M-2023 exists",
                    single_quarter="unchanged; 3 pre-existing live nulls (items 22, 23, 24: live 값_당분기 is null while the YTD difference would be %s) are NOT touched by the adoption and must stay blank (the 2023.2Q operand is a rounded disclosure value)"
                                   % ", ".join(str(x[2]) for x in model_mismatch)),
    "2023.2Q": dict(ytd_status="unchanged: master holds only 4 rounded disclosure cells (16, 22, 23, 24); the FY2024 Q2 report prints the old method", single_quarter="unchanged"),
    "2023.1Q": dict(ytd_status="unchanged: master (rounded disclosure) differs from the FY2024 Q1 report's prior column on items 1, 16, 17, 18 by about 8.5 eok (a reclassification between 보험손익 and 투자손익, 영업이익 equal); not a PL<->OCI move; not in the approved list",
                    single_quarter="unchanged"),
    "2025.1Q": dict(ytd_status="unchanged (not part of any restatement); single quarter = YTD", single_quarter="unchanged"),
}
plan["apply_contract"] = dict(
    gold_set_cells=[[CODE, c["item"], c["quarter"], c["new"], c["old"]] for c in cells],
    null_dangi_cells=[[CODE, s["quarter"], s["item"]] for s in seam_cells],
    set_dangi_cells=[],
    expected_master_changes=dict(
        value_cells_changed=len(cells),
        dangi_cells_changed=len([a for a in auto_follow if a.get("class") in ("both_adopted", None)]) + len(neighbour_effects) + len(seam_cells),
        dangi_cells_set_to_null=len(seam_cells),
        dangi_cells_changed_outside_bucket_values="2024.4Q items %s (derived from the adopted 2024.3Q YTD; the 4Q YTD itself is unchanged)" % ",".join(str(i) for i in POLICY_ITEMS)),
    do_not_touch=dict(owner_gold_cells=sorted([list(k) for k in GOLD]), csm_waterfall="unchanged for all four buckets (census SAME)",
                      items_not_in_cells="all other items, incl. 1, 16, 18, 21, 26, 28, 29, 30, 31, 32 (equal to the latest print), all Tier-2 items 2-15"),
    gate_notes="adopt 2024.1Q-2024.3Q together (their single quarters and the 2024.4Q single quarter depend on each other); 2023.4Q is independent of them but leaves the FY2023 block "
               "with Q4 restated and Q1-Q3 original -> 8 null_dangi cells on 2023.4Q")
(HERE / "plan_KR0032.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

L = []
for b in buckets:
    L.append(f"== {b['quarter']} adopt={b['adopt']} cells={b['n_cells']} items={b['items']} census_items_equal={b['items_equal_to_census']} gold_in_block={b['gold_cells_in_block']} overlap={b['gold_overlap_with_adopted_items']}")
    L.append(f"   later {b['later_filing']['fy']} rcept {b['later_filing']['rcept']} unit {b['later_filing']['unit']} col {b['later_filing']['column']} note_ok={b['later_filing']['restatement_note']['all_checked_cells_ok']}")
    for k in ("closure_master_before", "closure_merged_after", "closure_printed_later_filing"):
        L.append(f"   {k}:")
        for x in b[k]:
            L.append(f"      {x.get('name')}: " + ("SKIP" if 'resid' not in x else f"resid={x['resid']} strict_ok={x['ok']}" + (f" gate_ok={x['ok_gate']}" if 'ok_gate' in x else "")))
L.append("")
for c in cells:
    ns = c["note_table_source"]
    ts = c["third_xml_source"]
    L.append(f"CELL {c['quarter']} i{c['item']:>2} {c['item_name']}: old={c['old']} new={c['new']} delta={c['delta']} L{c['xml_line']} fsapi={c['census_new']} diff={c['second_source']['diff_vs_xml']} "
             f"mastEqOrig={c['master_equals_original_print']} note={'-' if not ns else (ns['after'], ns['ok_after'], ns['ok_before'])} third={'-' if not ts else (ts['value'], ts['ok'])}")
L.append("")
L.append(f"SEAM ({len(seam_cells)}):")
for s in seam_cells:
    L.append(f"   {s['quarter']} i{s['item']} old={s['old']} derived_after={s['derived_after_adoption']} -> {s['proposed']}")
L.append(f"NEIGHBOUR ({len(neighbour_effects)}):")
for s in neighbour_effects:
    L.append(f"   {s['quarter']} i{s['item']} class={s['class']} old={s['old']} after={s['derived_after_adoption']}")
L.append(f"AUTO_FOLLOW ({len(auto_follow)}):")
for s in auto_follow:
    L.append(f"   {s['quarter']} i{s['item']} {s.get('class', 'Q1')} old={s['old']} after={s.get('derived_after_adoption', s.get('derived_after'))}")
L.append("VERIFICATION " + json.dumps({k: v for k, v in verification.items() if k in ('master_equals_original_print_all', 'n_master_vs_original_cells', 'warnings', 'dangi_model_mismatch_vs_live_master', 'census_vs_xml', 'note_table_vs_xml', 'third_xml_source', 'gold')}, ensure_ascii=False, default=str))
p3 = verification["printed_three_month_check"]
L.append(f"3M check: n={p3['n']} ok={p3['n_ok']} max|diff|={p3['max_abs_diff']}")
for x in p3["rows"]:
    L.append(f"   {x['quarter']} i{x['item']} derived={x['derived']} printed3m={x['printed_3m']} diff={x['diff']} L{x['xml_line']} ok={x['ok']}")
L.append("2024.4Q master vs FY2024 annual current / FY2025 annual prior: equal both=%s ; not equal=%s" % (verification["q2024_4Q_master_vs_fy2024_current_and_fy2025_prior"]["items_equal_both"], verification["q2024_4Q_master_vs_fy2024_current_and_fy2025_prior"]["items_not_equal"]))
L.append("FY2023 YTD master vs FY2024 filings prior: " + json.dumps(fy23_summary, ensure_ascii=False))
L.append("FY2023 Q3 master vs original print: %d/%d equal" % (verification["fy2023_q3_master_vs_original_print"]["n_equal"], verification["fy2023_q3_master_vs_original_print"]["n"]))
L.append("2023.1Q unequal rows: " + json.dumps(nb_2023_1q, ensure_ascii=False))
(HERE / "KR0032_plan_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("done", len(cells), len(seam_cells), len(neighbour_effects), len(auto_follow), len(warnings))
