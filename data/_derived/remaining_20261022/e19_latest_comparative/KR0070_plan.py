# -*- coding: utf-8 -*-
"""KR0070 (ABL Life) latest-comparative adoption plan -- READ-ONLY on every master / gold / doc.
Independent re-read of the SEPARATE-basis statement of comprehensive income ("4-2. 포괄손익계산서") of the next-year filing (prior cumulative column)
and of the original filing (to prove master = original), closure on the merged vector, single-quarter (값_당분기) seam analysis.
Writes plan_KR0070.json + KR0070_plan_report.txt next to this script.  python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import KR0070_xml as X
ROOT = X.ROOT
sys.stdout.reconfigure(encoding="utf-8")
CODE, NAME = "KR0070", "ABL생명"
TOL_WON = 2e-5                      # equality tolerance (mn): won-precision print
TOL_ID = 0.002                      # identity tolerance (mn) = 2 thousand won

ITEM_NAME = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익",
             25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익",
             30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CHECK_ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32]      # 29 is empty in the master for KR0070 and not printed

RCEPT = {"FY2024_Q1": "20240516002045", "FY2024_Q2": "20240814004092", "FY2024_Q3": "20241114002738", "FY2024_Q4": "20250331001358",
         "FY2025_Q1": "20250515002435", "FY2025_Q2": "20250814004404", "FY2025_Q3": "20251114002593", "FY2025_Q4": "20260331003080"}
# orig = (filing, column position of the current-period CUMULATIVE value among the numeric cells: [3M cur, cum cur, 3M prior, cum prior])
SPEC = {
    "2024.1Q": dict(orig=("FY2024_Q1", 1), later=("FY2025_Q1", "PFY2024dFQA", "PFY2024dFQQ")),
    "2024.2Q": dict(orig=("FY2024_Q2", 1), later=("FY2025_Q2", "PFY2024dHYA", "PFY2024dHYQ")),
    "2024.3Q": dict(orig=("FY2024_Q3", 1), later=("FY2025_Q3", "PFY2024dTQA", "PFY2024dTQQ")),
}

HAS_LETTER = re.compile(r"[가-힣A-Za-z]")


def norm(label):
    s = (label or "").replace("\u3000", "").replace(" ", "")
    s = re.sub(r"^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]|[IVX]+)\.", "", s)
    s = re.sub(r"\(주[^)]*\)", "", s)
    s = s.replace("(손실)", "").replace("(수익)", "")
    return s


def build_index(rows):
    idx = defaultdict(list)
    for r in rows:
        g = {"label": r["label"][0] if r["label"] else "", "cells": [], "tr_line": r["tr_line"]}
        groups = [g]
        for c in r["cells"]:
            if c["ctx"] == "" and c["val"] is None and c["text"] and HAS_LETTER.search(c["text"]):
                g = {"label": c["text"], "cells": [], "tr_line": r["tr_line"]}
                groups.append(g)
            else:
                g["cells"].append(c)
        for gg in groups:
            idx[norm(gg["label"])].append(gg)
    return idx


def unit_of(rows):
    for r in rows[:10]:
        t = r["label"][0] if r["label"] else ""
        if "단위" in t:
            return "백만원" if "백만원" in t else ("원" if "원" in t else "?")
    return "?"


class Stmt:
    def __init__(self, fy):
        self.fy = fy
        self.title, self.end, self.rows = X.read_statement(fy)
        self.unit = unit_of(self.rows)
        self.idx = build_index(self.rows)
        self.rel = X.FILES[fy]

    def pick(self, names, ctx=None, pos=None):
        for n in names:
            gs = self.idx.get(n)
            if not gs:
                continue
            if len(gs) != 1:
                raise RuntimeError(f"{self.fy}: ambiguous label {n}: {len(gs)} groups")
            g = gs[0]
            if ctx is not None:
                cs = [c for c in g["cells"] if c["ctx"].startswith(ctx + "_") and "SeparateMember" in c["ctx"]]
                if len(cs) != 1:
                    raise RuntimeError(f"{self.fy}: {n} ctx {ctx}: {len(cs)} cells")
                c = cs[0]
            else:
                cs = [c for c in g["cells"] if c["val"] is not None]
                if len(cs) != 4:
                    raise RuntimeError(f"{self.fy}: {n}: expected 4 numeric cells, got {len(cs)}")
                c = cs[pos]
            if c["val"] is None:
                raise RuntimeError(f"{self.fy}: {n} value not numeric: {c['text']!r}")
            scale = 1e6 if self.unit == "원" else 1.0
            return dict(val=c["val"] / scale, raw=c["text"], line=c["line"], label=g["label"].replace("\u3000", " ").strip())
        raise KeyError(f"{self.fy}: none of {names}")


ITEM_LABELS = {
    1: ["보험손익"], 16: ["기타사업비용"], 17: ["투자손익"], 20: ["영업이익"], 21: ["영업외손익"], 22: ["법인세차감전순이익"], 23: ["법인세비용"],
    24: ["당기순이익", "분기순이익", "반기순이익"], 25: ["기타포괄손익"], 26: ["기타포괄손익-공정가치측정금융자산평가손익"],
    27: ["보험계약자산(부채)순금융손익"], 28: ["현금흐름위험회피파생상품평가손익"], 30: ["재보험계약자산(부채)순금융손익"],
    31: ["총포괄손익"], 32: ["기타포괄손익-공정가치측정신용손실"],
}


def P(p, sign):
    return dict(label=p["label"], line=p["line"], raw=p["raw"], sign=sign)


def read_items(st, ctx=None, pos=None):
    out = {}
    for it, names in ITEM_LABELS.items():
        p = st.pick(names, ctx, pos)
        out[it] = dict(val=p["val"], parts=[P(p, 1)])
    # 19 = (insurance finance income + reinsurance finance income) - (insurance finance expense + reinsurance finance expense); expense lines are printed positive
    a = st.pick(["보험금융수익"], ctx, pos)
    b = st.pick(["재보험금융수익"], ctx, pos)
    c = st.pick(["보험금융비용"], ctx, pos)
    d = st.pick(["재보험금융비용"], ctx, pos)
    out[19] = dict(val=a["val"] + b["val"] - c["val"] - d["val"], parts=[P(a, 1), P(b, 1), P(c, -1), P(d, -1)])
    out[18] = dict(val=out[17]["val"] - out[19]["val"], parts=[dict(label="derived 17-19", line=None, raw=None, sign=0)])
    # extra printed lines for cross checks (not adopted)
    e1 = st.pick(["영업외수익"], ctx, pos)
    e2 = st.pick(["영업외비용"], ctx, pos)
    out["nonop_income"] = dict(val=e1["val"], parts=[P(e1, 1)])
    out["nonop_expense"] = dict(val=e2["val"], parts=[P(e2, -1)])
    return out


# ------------------------------------------------------------------ masters
def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


pl_rows = load_json("PL_breakdown.json")
M = defaultdict(dict)
for r in pl_rows:
    if r["원보험사코드"] == CODE:
        M[r["항목번호"]][r["공시분기"]] = r
gold = load_json("data/_gold/user_pl_cells.json")
GOLD = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"] if e["원보험사코드"] == CODE}
NULL_D = {tuple(x) for x in gold.get("null_dangi", {}).get("cells", []) if x[0] == CODE}
SET_D = {tuple(x[:3]) for x in gold.get("set_dangi", {}).get("cells", []) if x[0] == CODE}
CONF = load_json("data/_gold/user_pl_confirmed_cells.json")
CONF_KR0070 = json.dumps(CONF, ensure_ascii=False).count(CODE)
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


cells, buckets, warnings = [], [], []
LATER_VAL, ORIG_VAL, LATER_3M = {}, {}, {}
for q, sp in SPEC.items():
    ofy, opos = sp["orig"]
    lfy, lctx, l3 = sp["later"]
    ORIG_VAL[q] = read_items(stmt(ofy), None, opos)
    LATER_VAL[q] = read_items(stmt(lfy), lctx, None)
    LATER_3M[q] = read_items(stmt(lfy), l3, None)
    for fy in (ofy, lfy):
        if stmt(fy).unit != "원":
            warnings.append(f"{fy}: unit {stmt(fy).unit} (expected 원)")

# ------------------------------------------------------------------ changed items per bucket
changed = {}
equal_items = {}
for q, sp in SPEC.items():
    ch, eq = [], []
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
        else:
            eq.append(it)
    changed[q] = ch
    equal_items[q] = eq

for q in SPEC:
    sp = SPEC[q]
    lfy, lctx, l3 = sp["later"]
    sl = stmt(lfy)
    cen = d5[(CODE, q)]["its"]
    for it in changed[q]:
        lat = LATER_VAL[q][it]
        old = mval(it, q)
        cn = cen[str(it)]
        cells.append(dict(
            quarter=q, item=it, item_name=ITEM_NAME[it], old=old, new=round(lat["val"], 6), delta=round(lat["val"] - old, 6),
            unit="백만원", source_unit=sl.unit, source_print="won (exact)",
            xml_file=sl.rel, xml_rcept=RCEPT[lfy], xml_period_column=lctx + " (separate/OFS statement, prior-period cumulative)",
            xml_line=lat["parts"][0]["line"],
            xml_lines=[dict(label=p["label"], line=p["line"], printed=p["raw"], sign=p["sign"]) for p in lat["parts"]],
            derivation=("direct print" if len(lat["parts"]) == 1 and lat["parts"][0]["sign"] == 1 else "sum of printed lines (signs in xml_lines)"),
            second_source=dict(kind="FS-API frmtrm column of the same filing (census d5_buckets.json)", value=cn["prior"], diff_vs_xml=round(cn["prior"] - lat["val"], 6)),
            census_new=cn["prior"], census_master=cn["master"],
            master_equals_original_print=abs(old - ORIG_VAL[q][it]["val"]) <= TOL_WON,
            original_print=dict(value=round(ORIG_VAL[q][it]["val"], 6), xml_file=stmt(sp["orig"][0]).rel, xml_line=ORIG_VAL[q][it]["parts"][0]["line"]),
            gold_cell=((CODE, it, q) in GOLD)))

for c in cells:
    lf = SPEC[c["quarter"]]["later"]
    c["gold_note"] = (f"2026-10-22 parser/ifrs17 (KR0070 최신 비교열 채택, owner 결정 2026-10-22, 교보생명 선례와 동일): 별도(OFS) 기준, {lf[0]} rcept {RCEPT[lf[0]]} 의 "
                      f"전기 누적 열({lf[1]}) = 재작성 값(FSS Q&A 보험금융손익 체계적 배분 변경). 원문 {c['xml_file']} L{c['xml_line']}" +
                      ("" if c["derivation"] == "direct print" else " 외 합산 줄(xml_lines)") +
                      f". 단위 {c['source_unit']}(정확 인쇄). 2차 근거 FS-API frmtrm 일치. 증거 data/_derived/remaining_20261022/e19_latest_comparative/plan_KR0070.json")


# ------------------------------------------------------------------ closure
def merged_vec(q, adopted=True):
    v = {it: mval(it, q) for it in range(1, 33)}
    if adopted:
        for c in cells:
            if c["quarter"] == q:
                v[c["item"]] = c["new"]
    return v


def closure(q, adopted):
    v = merged_vec(q, adopted)
    res = []

    def chk(name, lhs, rhs, note=None):
        if lhs is None or rhs is None:
            res.append(dict(name=name, status="SKIP (operand empty)"))
            return
        d = lhs - rhs
        r = dict(name=name, lhs=round(lhs, 6), rhs=round(rhs, 6), resid=round(d, 6), tol=TOL_ID, ok=abs(d) <= TOL_ID)
        if note:
            r["note"] = note
        res.append(r)

    chk("I1 20 = 1 + 17", v[20], v[1] + v[17])
    chk("I2 |22-24| = |23|", abs(v[22] - v[24]), abs(v[23]))
    chk("I2b 22 = 20 + 21", v[22], v[20] + v[21])
    chk("I3 31 = 24 + 25", v[31], v[24] + v[25])
    oci = [i for i in (26, 27, 28, 29, 30, 32) if v[i] is not None]
    chk("I4 25 = sum of OCI parts the master carries", v[25], sum(v[i] for i in oci), note="parts carried: %s (29 empty in master)" % oci)
    chk("I5 17 = 18 + 19", v[17], v[18] + v[19])
    bare = sum(x for x in (v[2], v[13], v[14]) if x is not None)
    adj = bare + (v[15] or 0) - (v[16] or 0)
    chk("I6 LOB bridge 1 = 2+13+14 + 15 - 16", v[1], adj, note="legs 2=%s 13=%s 14=%s 15=%s 16=%s" % (v[2], v[13], v[14], v[15], v[16]))
    # informational Tier-2 tree on the master (owner gold items 4 and 7 sit here)
    t2 = {}
    if all(v[i] is not None for i in (2, 3, 8)):
        t2["2 = 3 + 8"] = round(v[2] - v[3] - v[8], 6)
    if all(v[i] is not None for i in (3, 4, 5, 6, 7)):
        t2["3 = 4+5+6+7"] = round(v[3] - v[4] - v[5] - v[6] - v[7], 6)
    if all(v[i] is not None for i in (8, 9, 10, 11, 12)):
        t2["8 = 9+10+11+12"] = round(v[8] - v[9] - v[10] - v[11] - v[12], 6)
    res.append(dict(name="I7 Tier-2 tree (informational, unchanged by adoption)", resids=t2, ok=all(abs(x) <= TOL_ID for x in t2.values())))
    return res


def printed_closure(q):
    L = LATER_VAL[q]
    out = []

    def chk(n, a, b):
        out.append(dict(name=n, resid=round(a - b, 6), tol=TOL_ID, ok=abs(a - b) <= TOL_ID))

    chk("printed 20 = printed 1 + printed 17", L[20]["val"], L[1]["val"] + L[17]["val"])
    chk("printed 21 = nonop income - nonop expense", L[21]["val"], L["nonop_income"]["val"] - L["nonop_expense"]["val"])
    chk("printed 22 = printed 20 + printed 21", L[22]["val"], L[20]["val"] + L[21]["val"])
    chk("printed 24 = printed 22 - printed 23", L[24]["val"], L[22]["val"] - L[23]["val"])
    chk("printed 31 = printed 24 + printed 25", L[31]["val"], L[24]["val"] + L[25]["val"])
    chk("printed 25 = 26+27+28+30+32 (leaf rows)", L[25]["val"], sum(L[i]["val"] for i in (26, 27, 28, 30, 32)))
    return out


gold_overlap = {q: [it for it in changed[q] if (CODE, it, q) in GOLD] for q in SPEC}
gold_in_block = {q: sorted(it for (c, it, qq) in GOLD if qq == q) for q in SPEC}

for q in SPEC:
    ids_before, ids_after, pc = closure(q, False), closure(q, True), printed_closure(q)
    ok_after = all(x.get("ok", True) for x in ids_after) and all(x["ok"] for x in pc)
    sp = SPEC[q]
    census_items = sorted(int(k) for k, v in d5[(CODE, q)]["its"].items() if abs(v["prior"] - v["master"]) > 1e-3)
    adopt = bool(ok_after and not gold_overlap[q] and d5[(CODE, q)]["csm"]["status"] == "SAME")
    buckets.append(dict(
        quarter=q, adopt=adopt, n_cells=len(changed[q]), items=changed[q], items_equal_to_later_print=equal_items[q],
        original_filing=dict(fy=sp["orig"][0], rcept=RCEPT[sp["orig"][0]], file=stmt(sp["orig"][0]).rel, statement_title_line=stmt(sp["orig"][0]).title),
        later_filing=dict(fy=sp["later"][0], rcept=RCEPT[sp["later"][0]], file=stmt(sp["later"][0]).rel, statement_title_line=stmt(sp["later"][0]).title,
                          unit=stmt(sp["later"][0]).unit, column=sp["later"][1], three_month_column=sp["later"][2]),
        census_items=census_items, items_equal_to_census=(census_items == changed[q]),
        gold_cells_in_block=gold_in_block[q], gold_overlap_with_adopted_items=gold_overlap[q],
        user_pl_confirmed_cells_mentions_of_code=CONF_KR0070,
        closure_master_before=ids_before, closure_merged_after=ids_after, closure_printed_later_filing=pc,
        csm_vs_master=d5[(CODE, q)]["csm"]["status"],
        reason=("closes on the merged vector; no owner gold cell among the changed items; CSM latest = master (SAME), PL4/CSM5 pair untouched" if adopt
                else "NOT CLOSED or gold overlap or CSM differs -- see closure lists")))


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


def latest_flag(item, q):
    if (item, q) in adopted_new:
        return "adopted"
    b = d5.get((CODE, q))
    if b is not None:
        c = b["cls"].get(str(item))
        return "equal_to_latest" if c == "EQ" else ("differs_from_latest" if c else "n/a")
    return "n/a"


# model check over ALL items of the three FYs: derived(YTD master) == live 값_당분기 (so that the derivation rule used below is the production one)
for item in range(1, 33):
    for fy in ("2023", "2024"):
        qs = [f"{fy}.{n}Q" for n in (1, 2, 3, 4)]
        ytd = {q: mval(item, q) for q in qs}
        for q in qs:
            dm, dl = derived(ytd, q), mdangi(item, q)
            if (dm is None) != (dl is None) or (dm is not None and abs(dm - dl) > 1e-5):
                model_mismatch.append((item, q, dm, dl))

for item in POLICY_ITEMS:
    for fy in ("2024",):
        qs = [f"{fy}.{n}Q" for n in (1, 2, 3, 4)]
        ytd_b = {q: mval(item, q) for q in qs}
        ytd_a = {q: adopted_new.get((item, q), mval(item, q)) for q in qs}
        for q in qs:
            db_model, db_live, da = derived(ytd_b, q), mdangi(item, q), derived(ytd_a, q)
            n = int(q[5])
            cur_changed = (item, q) in adopted_new
            prev_changed = n > 1 and (item, f"{fy}.{n-1}Q") in adopted_new
            if not cur_changed and not prev_changed:
                continue
            if n == 1:
                auto_follow.append(dict(quarter=q, item=item, old=db_live, derived_after=da, why="Q1 single quarter = YTD of the same bucket"))
                continue
            pq = f"{fy}.{n-1}Q"
            vc, vp = latest_flag(item, q), latest_flag(item, pq)
            rec = dict(quarter=q, item=item, item_name=ITEM_NAME[item], old=db_live, derived_after_adoption=da,
                       operand_cur=dict(q=q, ytd_before=ytd_b[q], ytd_after=ytd_a[q], status=vc),
                       operand_prev=dict(q=pq, ytd_before=ytd_b[pq], ytd_after=ytd_a[pq], status=vp))
            if cur_changed and prev_changed:
                rec["class"] = "both_adopted"
                auto_follow.append(rec)
            elif cur_changed and not prev_changed and vp != "equal_to_latest":
                rec["class"] = "seam"
                rec["proposed"] = "null_dangi"
                rec["printed_three_month_column_in_later_filing"] = False
                rec["reason"] = "current YTD adopted, previous YTD stays at another vintage"
                seam_cells.append(rec)
            elif (not cur_changed) and prev_changed:
                rec["class"] = "consistent_after_adoption" if vc == "equal_to_latest" else "pre_existing_difference_outside_scope"
                neighbour_effects.append(rec)
            else:
                rec["class"] = "other"
                neighbour_effects.append(rec)

# derived single quarter after adoption vs the 3-month column printed in the later filing (second, independent print)
dangi_vs_printed = []
for q in SPEC:
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
                                     xml_file=stmt(SPEC[q]["later"][0]).rel, tol=TOL_ID, ok=abs(da - p3["val"]) <= TOL_ID))

# 2024.4Q: master (annual print) vs the annual print itself and vs the FY2025 annual prior column
s24 = stmt("FY2024_Q4")
s25 = stmt("FY2025_Q4")
v24 = read_items(s24, "CFY2024dFY", None)
v25 = read_items(s25, "PFY2024dFY", None)
q4rows = []
for it in sorted(set(CHECK_ITEMS)):
    m = mval(it, "2024.4Q")
    q4rows.append(dict(item=it, master=m, fy2024_annual_current_print=round(v24[it]["val"], 6), fy2025_annual_prior_print=round(v25[it]["val"], 6),
                       master_eq_annual_print=abs(m - v24[it]["val"]) <= TOL_WON, master_eq_fy2025_prior=abs(m - v25[it]["val"]) <= TOL_WON,
                       diff_vs_fy2025_prior=round(m - v25[it]["val"], 6), xml_line_fy2024=v24[it]["parts"][0]["line"], xml_line_fy2025=v25[it]["parts"][0]["line"]))
q4_single = {}
for item in (17, 19, 20, 22, 23, 24, 25, 26, 27, 31, 32):
    yb = {q: mval(item, q) for q in (f"2024.{n}Q" for n in (1, 2, 3, 4))}
    ya = {q: adopted_new.get((item, q), mval(item, q)) for q in yb}
    q4_single[item] = dict(live_dangi=mdangi(item, "2024.4Q"), derived_after_adoption=derived(ya, "2024.4Q"), ytd4_master=yb["2024.4Q"], ytd3_before=yb["2024.3Q"], ytd3_after=ya["2024.3Q"],
                           ytd4_fy2025_annual_prior=round(v25[item]["val"], 6))

# 2025 neighbours: master vs the print of the same filing (current column) -> same vintage as the adopted 2024 prior columns
n25 = []
for q, fy, ctx in (("2025.1Q", "FY2025_Q1", "CFY2025dFQA"), ("2025.2Q", "FY2025_Q2", "CFY2025dHYA"), ("2025.3Q", "FY2025_Q3", "CFY2025dTQA")):
    v = read_items(stmt(fy), ctx, None)
    for it in CHECK_ITEMS:
        m = mval(it, q)
        if m is None:
            continue
        n25.append(dict(quarter=q, item=it, master=m, filing_print=round(v[it]["val"], 6), equal=abs(m - v[it]["val"]) <= TOL_WON))

# 2023.4Q: master vs FY2024 annual prior column (informational; NOT in this task, CSM gold)
v23 = read_items(stmt("FY2024_Q4"), "PFY2023dFY", None)
n23 = [dict(item=it, master=mval(it, "2023.4Q"), fy2024_annual_prior=round(v23[it]["val"], 6), equal=abs(mval(it, "2023.4Q") - v23[it]["val"]) <= TOL_WON) for it in CHECK_ITEMS if mval(it, "2023.4Q") is not None]

verification = dict(
    master_equals_original_print_all=all(abs(mval(it, q) - ORIG_VAL[q][it]["val"]) <= TOL_WON for q in SPEC for it in CHECK_ITEMS if mval(it, q) is not None),
    warnings=warnings, dangi_model_mismatch_vs_live_master=model_mismatch,
    census_vs_xml=dict(n_cells=len(cells), max_abs_diff=max(abs(c["second_source"]["diff_vs_xml"]) for c in cells), items_equal_to_census_all_buckets=all(b["items_equal_to_census"] for b in buckets)),
    gold=dict(KR0070_gold_set_cells=len(GOLD), KR0070_gold_set_keys=sorted([list(k) for k in GOLD]), adopted_cells_hitting_gold=[(c["quarter"], c["item"]) for c in cells if c["gold_cell"]],
              user_pl_confirmed_cells_mentions_of_KR0070=CONF_KR0070, null_dangi_existing=sorted(NULL_D), set_dangi_existing=sorted(SET_D)),
    printed_three_month_check=dict(n=len(dangi_vs_printed), n_ok=sum(1 for x in dangi_vs_printed if x["ok"]),
                                   max_abs_diff=max(abs(x["diff"]) for x in dangi_vs_printed) if dangi_vs_printed else None, rows=dangi_vs_printed),
    q2024_4Q=dict(rows=q4rows, items_master_eq_annual_print=[r["item"] for r in q4rows if r["master_eq_annual_print"]],
                  items_differing_from_fy2025_prior=[r["item"] for r in q4rows if not r["master_eq_fy2025_prior"]], single_quarter=q4_single),
    q2025_master_vs_own_print=dict(n=len(n25), n_equal=sum(1 for x in n25 if x["equal"]), differing=[(x["quarter"], x["item"], x["master"], x["filing_print"]) for x in n25 if not x["equal"]]),
    q2023_4Q_master_vs_fy2024_annual_prior_informational=dict(equal_items=[x["item"] for x in n23 if x["equal"]], differing_items=[x["item"] for x in n23 if not x["equal"]]),
)
plan = dict(code=CODE, company=NAME, generated="2026-10-22", source_tool="data/_derived/remaining_20261022/e19_latest_comparative/KR0070_plan.py", master_unit="백만원",
            statement="separate (OFS) 4-2. 포괄손익계산서, prior-period cumulative column of the next-year filing", buckets=buckets, cells=cells,
            seam_cells=seam_cells, neighbour_effects=neighbour_effects, auto_follow_cells=auto_follow, verification=verification)
plan["apply_contract"] = dict(
    gold_set_cells=[[CODE, c["item"], c["quarter"], c["new"], c["old"]] for c in cells],
    null_dangi_cells=[[CODE, s["quarter"], s["item"]] for s in seam_cells],
    set_dangi_cells=[],
    expected_master_changes=dict(
        value_cells_changed=len(cells),
        dangi_cells_changed=len(cells) + len(neighbour_effects),
        dangi_cells_set_to_null=len(seam_cells),
        dangi_cells_changed_outside_bucket_values="2024.4Q items %s (derived from the adopted 2024.3Q YTD; 4Q YTD itself unchanged)" % sorted({n["item"] for n in neighbour_effects})),
    do_not_touch=dict(owner_gold_cells=sorted([list(k) for k in GOLD]), csm_waterfall="unchanged for the three buckets (census SAME)",
                      items_not_in_cells="all other items, incl. 1, 16, 18, 21, 26, 28, 30, 32 (equal to the latest print to the won)"),
    gate_notes="adopt 2024.1Q-3Q together (2Q and 3Q single quarters need both YTD operands at the new vintage); 2024.4Q annual is already at the new vintage for items 1-24, 27, 28, 30, 32")
(HERE / "plan_KR0070.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

L = []
for b in buckets:
    L.append(f"== {b['quarter']} adopt={b['adopt']} cells={b['n_cells']} items={b['items']} equal_items={b['items_equal_to_later_print']} census_items_equal={b['items_equal_to_census']} gold_in_block={b['gold_cells_in_block']} overlap={b['gold_overlap_with_adopted_items']}")
    L.append(f"   later {b['later_filing']['fy']} rcept {b['later_filing']['rcept']} unit {b['later_filing']['unit']} col {b['later_filing']['column']}")
    for k in ("closure_master_before", "closure_merged_after", "closure_printed_later_filing"):
        L.append(f"   {k}:")
        for x in b[k]:
            L.append(f"      {x.get('name')}: " + ("SKIP" if ('resid' not in x and 'resids' not in x) else (f"resids={x['resids']} ok={x['ok']}" if 'resids' in x else f"resid={x['resid']} tol={x['tol']} ok={x['ok']}")))
L.append("")
for c in cells:
    L.append(f"CELL {c['quarter']} i{c['item']:>2} {c['item_name']}: old={c['old']} new={c['new']} delta={c['delta']} L{c['xml_line']} fsapi={c['census_new']} diff={c['second_source']['diff_vs_xml']} mastEqOrig={c['master_equals_original_print']} deriv={c['derivation']}")
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
L.append("VERIFICATION " + json.dumps({k: v for k, v in verification.items() if k not in ('printed_three_month_check', 'q2024_4Q')}, ensure_ascii=False, default=str))
p3 = verification["printed_three_month_check"]
L.append(f"3M check: n={p3['n']} ok={p3['n_ok']} max|diff|={p3['max_abs_diff']}")
for x in p3["rows"]:
    L.append(f"   {x['quarter']} i{x['item']} derived={x['derived']} printed3m={x['printed_3m']} diff={x['diff']} L{x['xml_line']} ok={x['ok']}")
L.append("2024.4Q master vs annual prints:")
for r in q4rows:
    L.append("   " + json.dumps(r, ensure_ascii=False))
L.append("2024.4Q single quarter:")
for k, v in q4_single.items():
    L.append(f"   i{k} " + json.dumps(v, ensure_ascii=False))
(HERE / "KR0070_plan_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("done", len(cells), len(seam_cells), len(neighbour_effects), len(auto_follow), len(warnings), len(model_mismatch))
