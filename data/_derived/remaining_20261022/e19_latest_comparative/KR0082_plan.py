# -*- coding: utf-8 -*-
"""KR0082 (DB Life) latest-comparative adoption plan for bucket 2023.3Q -- READ-ONLY on every master / gold / doc.
Independent re-read (own XML reader KR0082_xml.py, no scripts/ or src/ imports) of the SEPARATE-basis statement of comprehensive income
('4-2. 포괄손익계산서', section '4. 재무제표') of
  * the original filing   FY2023_Q3 (rcept 20231114002805), cumulative current column     -> proves master = original print
  * the later filing      FY2024_Q3 (rcept 20241114001831), prior-year cumulative column  -> adoption values, prior-year 3-month column -> set_dangi
  * neighbours            FY2024_Q1 / FY2024_Q2 prior columns (2023.1Q / 2023.2Q, not approved), FY2023_Q4 / FY2024_Q4 (2023.4Q annual)
Closure on the merged vector, single quarter (값_당분기) seam analysis, year tie.
Writes plan_KR0082.json + KR0082_plan_report.txt next to this script.  python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import KR0082_xml as X
ROOT = X.ROOT
sys.stdout.reconfigure(encoding="utf-8")
CODE, NAME = "KR0082", "DB생명"
TOL_WON = 2e-5                      # equality tolerance (mn): won-precision print
TOL_ID = 0.002                      # identity tolerance (mn) = 2 thousand won

ITEM_NAME = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익",
             25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익",
             30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CHECK_ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

RCEPT = {"FY2023_Q1": "20230515002932", "FY2023_Q2": "20230814002739", "FY2023_Q3": "20231114002805", "FY2023_Q4": "20240329001728",
         "FY2024_Q1": "20240514000901", "FY2024_Q2": "20240814000663", "FY2024_Q3": "20241114001831", "FY2024_Q4": "20250328002241"}
# orig = (filing, position of the current-period CUMULATIVE value among the numeric cells, number of cells)
SPEC = {
    "2023.1Q": dict(later=("FY2024_Q1", 3, 2, 4), approved=False),
    "2023.2Q": dict(later=("FY2024_Q2", 3, 2, 4), approved=False),
    "2023.3Q": dict(orig=("FY2023_Q3", 1, 4), orig3m=("FY2023_Q3", 0, 4), later=("FY2024_Q3", 3, 2, 4), approved=True),     # later = (filing, cum-prior pos, 3m-prior pos, ncells)
}
APPROVED = [q for q, s in SPEC.items() if s["approved"]]
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
            if c["ctx"] == "" and c["val"] is None and c["text"] and c["text"].strip() != "-" and HAS_LETTER.search(c["text"]):
                g = {"label": c["text"], "cells": [], "tr_line": r["tr_line"]}
                groups.append(g)
            else:
                g["cells"].append(c)
        for gg in groups:
            idx[norm(gg["label"])].append(gg)
    return idx


def unit_of(rows):
    for r in rows[:12]:
        t = r["label"][0] if r["label"] else ""
        if "단위" in t:
            return "백만원" if "백만원" in t else ("원" if "원" in t else "?")
    return "?"


def cell_val(c):
    if c["val"] is not None:
        return c["val"]
    if c["text"].strip() == "-":
        return 0.0
    raise RuntimeError(f"value not numeric: {c['text']!r}")


class Stmt:
    def __init__(self, fy):
        self.fy = fy
        self.title, self.end, self.rows = X.read_statement(fy)
        self.unit = unit_of(self.rows)
        self.idx = build_index(self.rows)
        self.rel = X.FILES[fy]
        self.scale = 1e6 if self.unit == "원" else 1.0
        lines = X.load_lines(fy)
        # parent section: the last '<TITLE' with 'N. ' (level-1) before the statement title
        self.parent = None
        for i in range(self.title - 1, 0, -1):
            if lines[i - 1].startswith("<TITLE") and re.search(r">\s*\d\. [^<]*재무제표[^<]*<", lines[i - 1]) and "-" not in re.sub(r"<[^>]+>", "", lines[i - 1])[:4]:
                self.parent = (i, re.sub(r"<[^>]+>", "", lines[i - 1]).strip())
                break

    def group(self, names):
        for n in names:
            gs = self.idx.get(n)
            if not gs:
                continue
            if len(gs) != 1:
                raise RuntimeError(f"{self.fy}: ambiguous label {n}: {len(gs)} groups")
            return gs[0]
        return None

    def pick(self, names, pos, ncells, optional=False, want_ctx=None):
        g = self.group(names)
        if g is None:
            if optional:
                return None
            raise KeyError(f"{self.fy}: none of {names}")
        cs = [c for c in g["cells"] if c["text"] != ""]
        if len(cs) != ncells:
            raise RuntimeError(f"{self.fy}: {g['label']}: expected {ncells} cells, got {len(cs)}")
        c = cs[pos]
        if want_ctx is not None and not (c["ctx"].startswith(want_ctx + "_") and "SeparateMember" in c["ctx"]):
            raise RuntimeError(f"{self.fy}: {g['label']}: ctx {c['ctx']} != {want_ctx} separate")
        return dict(printed=cell_val(c), raw=c["text"], line=c["line"], label=g["label"].replace("\u3000", " ").strip(), ctx=c["ctx"])

    def oci_leaf_rows(self, pos, ncells):
        out, on = [], False
        for r in self.rows:
            lab = norm(r["label"][0] if r["label"] else "")
            if lab == "기타포괄손익":
                on = True
                continue
            if lab == "총포괄손익":
                break
            if on and not (lab.startswith("당기손익으로재분류") or lab.startswith("후속적으로")):
                cs = [c for c in r["cells"] if c["text"] != ""]
                if len(cs) != ncells:
                    raise RuntimeError(f"{self.fy}: oci leaf {r['label']}: {len(cs)} cells")
                c = cs[pos]
                out.append(dict(label=r["label"][0], printed=cell_val(c), val=cell_val(c) / self.scale, line=c["line"], raw=c["text"]))
        return out


ITEM_LABELS = {
    1: ["보험손익"], 17: ["투자손익"], 20: ["영업이익"], 21: ["영업외손익"], 22: ["법인세차감전순이익"],
    24: ["당기순이익", "분기순이익", "반기순이익"], 25: ["기타포괄손익"],
    26: ["기타포괄손익-공정가치측정금융자산관련손익", "기타포괄손익-공정가치측정채무증권평가손익", "기타포괄손익-공정가치측정금융자산평가손익"],
    27: ["보험계약자산(부채)순금융손익"], 28: ["현금흐름위험회피파생상품평가손익", "위험회피목적파생상품평가손익"],
    29: ["기타포괄손익-공정가치측정유가증권평가손익", "기타포괄손익-공정가치측정지분증권평가손익", "기타포괄손익-공정가치측정지분상품평가손익"],
    30: ["재보험계약자산(부채)순금융손익"], 31: ["총포괄손익"],
}


def part(p, contribution_mn):
    return dict(label=p["label"], line=p["line"], printed=p["raw"], contribution_mn=round(contribution_mn, 6))


def read_items(st, pos, ncells, want_ctx=None):
    """-> dict item -> dict(val (백만원, master sign convention), parts[...]) plus helper entries.  Expenses are printed negative in the 2023 filings and
    positive in the 2024 filings; conv = -1 when 보험서비스비용 is printed negative, the master carries expenses positive."""
    sc = st.scale

    def pk(names, optional=False):
        return st.pick(names, pos, ncells, optional, want_ctx)

    svc = pk(["보험서비스비용"])
    conv = -1 if svc["printed"] < 0 else 1
    out = {"_conv": conv}

    def direct(it, names):
        p = pk(names)
        out[it] = dict(val=p["printed"] / sc, parts=[part(p, p["printed"] / sc)])

    for it in (1, 17, 20, 21, 22, 24, 25, 26, 27, 28, 29, 30, 31):
        direct(it, ITEM_LABELS[it])
    # expense items: master positive
    p16 = pk(["기타사업비용"])
    out[16] = dict(val=conv * p16["printed"] / sc, parts=[part(p16, conv * p16["printed"] / sc)])
    p23 = pk(["법인세비용"])
    out[23] = dict(val=conv * p23["printed"] / sc, parts=[part(p23, conv * p23["printed"] / sc)])
    # 19 = (보험금융수익 + 재보험금융수익) - (보험금융비용 + 재보험금융비용)
    comps = [("보험금융수익", 1), ("재보험금융수익", 1), ("보험금융비용", -1), ("재보험금융비용", -1)]
    parts, v19 = [], 0.0
    for nm, sg in comps:
        p = pk([nm])
        contrib = (p["printed"] / sc) if sg == 1 else -(conv * p["printed"] / sc)
        v19 += contrib
        parts.append(part(p, contrib))
    out[19] = dict(val=v19, parts=parts)
    # 18 = 17 - 19 (production definition, gross investment result)
    out[18] = dict(val=out[17]["val"] - out[19]["val"],
                   parts=[dict(p, label=p["label"]) for p in out[17]["parts"]] + [dict(p, contribution_mn=-p["contribution_mn"]) for p in out[19]["parts"]])
    # 32 = 25 - (26+27+28+29+30) (production definition: residual OCI)
    out[32] = dict(val=out[25]["val"] - sum(out[i]["val"] for i in (26, 27, 28, 29, 30)),
                   parts=[dict(out[25]["parts"][0])] + [dict(out[i]["parts"][0], contribution_mn=-out[i]["parts"][0]["contribution_mn"]) for i in (26, 27, 28, 29, 30)])
    # helper lines for the independent alternative paths
    h = {}
    for key, nm, is_exp in (("rev_ins", "보험영업수익", False), ("ins_rev", "보험수익", False), ("reins_rev", "재보험수익", False), ("svc", "보험서비스비용", True), ("ins_cost", "보험비용", True), ("reins_cost", "재보험비용", True),
                            ("inv_rev", "투자영업수익", False), ("inv_cost", "투자영업비용", True), ("nonop_inc", "영업외수익", False), ("nonop_exp", "영업외비용", True)):
        p = pk([nm])
        h[key] = dict(val=(conv * p["printed"] if is_exp else p["printed"]) / sc, line=p["line"], raw=p["raw"], label=p["label"])
    out["_h"] = h
    leafs = st.oci_leaf_rows(pos, ncells)
    out["_leafs"] = leafs
    out["_leaf_sum"] = sum(x["val"] for x in leafs)
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
CONF_N = json.dumps(CONF, ensure_ascii=False).count(CODE)
d5 = {(b["code"], b["q"]): b for b in load_json("data/_derived/remaining_20261022/d_census/d5_buckets.json")}
cand = {(c[1], c[2]): c for c in load_json("data/_derived/remaining_20261022/d_census/cand_pl_cells.json") if c[0] == CODE}
csm_rows = [r for r in load_json("CSM_waterfall.json") if r["원보험사코드"] == CODE]


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
LATER_VAL, ORIG_VAL, LATER_3M, ORIG_3M = {}, {}, {}, {}
for q, sp in SPEC.items():
    lfy, lcum, l3, nc = sp["later"]
    LATER_VAL[q] = read_items(stmt(lfy), lcum, nc)
    LATER_3M[q] = read_items(stmt(lfy), l3, nc)
    fys = [lfy]
    if "orig" in sp:
        ofy, opos, onc = sp["orig"]
        ORIG_VAL[q] = read_items(stmt(ofy), opos, onc)
        ORIG_3M[q] = read_items(stmt(ofy), sp["orig3m"][1], sp["orig3m"][2])
        fys.append(ofy)
    for fy in fys:
        if stmt(fy).unit != "원":
            warnings.append(f"{fy}: unit {stmt(fy).unit} (expected 원)")

# ------------------------------------------------------------------ changed items per bucket (later cumulative print vs master)
changed, equal_items = {}, {}
for q, sp in SPEC.items():
    ch, eq = [], []
    for it in CHECK_ITEMS:
        old = mval(it, q)
        if old is None:
            continue
        if "orig" in sp:
            org = ORIG_VAL[q][it]["val"]
            if abs(old - org) > TOL_WON:
                warnings.append(f"{q} item {it}: master {old} != original print {org}" + (" (owner gold cell)" if (CODE, it, q) in GOLD else ""))
        if abs(LATER_VAL[q][it]["val"] - old) > TOL_WON:
            ch.append(it)
        else:
            eq.append(it)
    changed[q], equal_items[q] = ch, eq


def alt_path(L, it):
    """independent arithmetic path from other printed lines of the same column; returns (value, formula, lines)"""
    h = L["_h"]
    if it == 1:
        return h["rev_ins"]["val"] - h["svc"]["val"], "보험영업수익 - 보험서비스비용", [h["rev_ins"], h["svc"]]
    if it == 16:
        return h["svc"]["val"] - h["ins_cost"]["val"] - h["reins_cost"]["val"], "보험서비스비용 - 보험비용 - 재보험비용", [h["svc"], h["ins_cost"], h["reins_cost"]]
    if it == 17:
        return h["inv_rev"]["val"] - h["inv_cost"]["val"], "투자영업수익 - 투자영업비용", [h["inv_rev"], h["inv_cost"]]
    if it == 18:
        # gross investment result = investment revenue - 보험금융수익 - 재보험금융수익 - (investment cost - 보험금융비용 - 재보험금융비용)
        pr = {p["label"]: p for p in L[19]["parts"]}
        fin_inc = sum(p["contribution_mn"] for p in L[19]["parts"] if p["contribution_mn"] > 0 and "수익" in p["label"])
        fin_exp = -sum(p["contribution_mn"] for p in L[19]["parts"] if "비용" in p["label"])
        return h["inv_rev"]["val"] - fin_inc - (h["inv_cost"]["val"] - fin_exp), "투자영업수익 - (보험금융수익+재보험금융수익) - [투자영업비용 - (보험금융비용+재보험금융비용)]", [h["inv_rev"], h["inv_cost"]] + L[19]["parts"]
    return None


for q in APPROVED:
    sp = SPEC[q]
    lfy, lcum, l3, nc = sp["later"]
    sl = stmt(lfy)
    cen = d5[(CODE, q)]["its"]
    for it in changed[q]:
        lat = LATER_VAL[q][it]
        old = mval(it, q)
        cn = cen[str(it)]
        ap = alt_path(LATER_VAL[q], it)
        cells.append(dict(
            quarter=q, item=it, item_name=ITEM_NAME[it], old=old, new=round(lat["val"], 6), delta=round(lat["val"] - old, 6),
            unit="백만원", source_unit=sl.unit, source_print="won (exact)",
            xml_file=sl.rel, xml_rcept=RCEPT[lfy], xml_period_column="prior-year cumulative column (9M 2023) of the separate/OFS 4-2 statement; 4 numeric cells [3M cur, cum cur, 3M prior, cum prior], position 4",
            xml_line=lat["parts"][0]["line"],
            xml_lines=[dict(label=p["label"], line=p["line"], printed=p["printed"], contribution_mn=p["contribution_mn"]) for p in lat["parts"]],
            derivation=("direct print" if len(lat["parts"]) == 1 else ("derived item 18 = item 17 - item 19 (production definition; contributions in xml_lines)" if it == 18 else "sum of printed lines (contributions in xml_lines)")),
            sign_note=("expenses are printed positive in this (2024) filing, negative in the original (2023) filing; master carries expenses positive: contribution = printed" if it in (16, 19, 18) else None),
            second_source=dict(
                fsapi=dict(kind="DART FS-API frmtrm column of the same FY2024 Q3 filing (census d5_buckets.json prior)", value=cn["prior"], diff_vs_xml=round(cn["prior"] - lat["val"], 6)),
                alt_path=(None if ap is None else dict(kind="independent arithmetic path from other printed lines of the same column", formula=ap[1], value=round(ap[0], 6), diff_vs_xml=round(ap[0] - lat["val"], 6), ok=abs(ap[0] - lat["val"]) <= TOL_ID,
                                                      lines=[dict(label=x["label"], line=x["line"], printed=x.get("raw") or x.get("printed")) for x in ap[2]])),
            ),
            census_new=cn["prior"], census_master=cn["master"], census_candidate_new=(cand[(q, it)][4] if (q, it) in cand else None),
            census_candidate_diff_vs_xml=(round(cand[(q, it)][4] - lat["val"], 6) if (q, it) in cand else None),
            master_equals_original_print=abs(old - ORIG_VAL[q][it]["val"]) <= TOL_WON,
            original_print=dict(value=round(ORIG_VAL[q][it]["val"], 6), xml_file=stmt(sp["orig"][0]).rel, xml_line=ORIG_VAL[q][it]["parts"][0]["line"], rcept=RCEPT[sp["orig"][0]]),
            gold_cell=((CODE, it, q) in GOLD)))

for c in cells:
    lf = SPEC[c["quarter"]]["later"]
    d = c["delta"]
    c["gold_note"] = (f"2026-10-22 parser/ifrs17 (KR0082 최신 비교열 채택, owner 결정 2026-10-22, 교보생명 선례와 동일): 별도(OFS) 기준 4-2 포괄손익계산서, {lf[0]} rcept {RCEPT[lf[0]]} 의 "
                      f"전기(2023.9.30 누적) 열 = {c['new']} 백만원. 원문 {c['xml_file']} L{c['xml_line']}" +
                      ("" if c["derivation"] == "direct print" else " 외 합산 줄(xml_lines)") +
                      f". 단위 원(정확 인쇄). 현재 마스터값 {c['old']} 는 원 공시 FY2023_Q3 rcept {RCEPT['FY2023_Q3']} 인쇄값과 일치. 변동 {d:+.6f}: 후속 공시 비교열에서 기타사업비용 일부 1,885.207774 백만원이 "
                      f"보험서비스비용에서 투자영업비용으로 옮겨 인쇄됨(보험서비스비용 -1,885.207774 = 투자영업비용 +1,885.207774, 영업이익 불변). 재작성 사유 주석은 해당 공시에서 찾지 못함. "
                      f"2차 근거 FS-API frmtrm 일치 및 같은 열의 다른 인쇄 줄에 의한 독립 산식 일치. 증거 data/_derived/remaining_20261022/e19_latest_comparative/plan_KR0082.json")


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

    def S(*xs):
        return None if any(x is None for x in xs) else sum(xs)

    chk("I1 20 = 1 + 17", v[20], S(v[1], v[17]))
    chk("I2 |22-24| = |23|", None if v[22] is None or v[24] is None else abs(v[22] - v[24]), None if v[23] is None else abs(v[23]))
    chk("I2b 22 = 20 + 21", v[22], S(v[20], v[21]))
    chk("I3 31 = 24 + 25", v[31], S(v[24], v[25]))
    oci = [i for i in (26, 27, 28, 29, 30, 32) if v[i] is not None]
    chk("I4 25 = sum of OCI parts the master carries", v[25], S(*[v[i] for i in oci]) if oci else None, note="parts carried: %s" % oci)
    chk("I5 17 = 18 + 19", v[17], S(v[18], v[19]))
    bare = sum(x for x in (v[2], v[13], v[14]) if x is not None)
    adj = bare + (v[15] or 0) - (v[16] or 0)
    chk("I6 LOB bridge 1 = 2+13+14 + 15 - 16 (master Tier-2 legs)", v[1], adj, note="legs 2=%s 13=%s 14=%s 15=%s 16=%s" % (v[2], v[13], v[14], v[15], v[16]))
    t2 = {}
    if all(v[i] is not None for i in (2, 3, 8)):
        t2["2 = 3 + 8"] = round(v[2] - v[3] - v[8], 6)
    if all(v[i] is not None for i in (3, 4, 5, 6, 7)):
        t2["3 = 4+5+6+7"] = round(v[3] - v[4] - v[5] - v[6] - v[7], 6)
    if all(v[i] is not None for i in (8, 9, 10, 11, 12)):
        t2["8 = 9+10+11+12"] = round(v[8] - v[9] - v[10] - v[11] - v[12], 6)
    res.append(dict(name="I7 Tier-2 tree (informational, unchanged by adoption)", resids=t2, ok=all(abs(x) <= TOL_ID for x in t2.values())))
    return res


def printed_closure(L):
    h = L["_h"]
    out = []

    def chk(n, a, b):
        out.append(dict(name=n, resid=round(a - b, 6), tol=TOL_ID, ok=abs(a - b) <= TOL_ID))

    chk("printed 보험영업수익 = 보험수익 + 재보험수익", h["rev_ins"]["val"], h["ins_rev"]["val"] + h["reins_rev"]["val"])
    chk("printed 보험손익 = 보험영업수익 - 보험서비스비용", L[1]["val"], h["rev_ins"]["val"] - h["svc"]["val"])
    chk("printed 보험서비스비용 = 보험비용 + 재보험비용 + 기타사업비용", h["svc"]["val"], h["ins_cost"]["val"] + h["reins_cost"]["val"] + L[16]["val"])
    chk("printed 투자손익 = 투자영업수익 - 투자영업비용", L[17]["val"], h["inv_rev"]["val"] - h["inv_cost"]["val"])
    chk("printed 20 = printed 1 + printed 17", L[20]["val"], L[1]["val"] + L[17]["val"])
    chk("printed 21 = nonop income - nonop expense", L[21]["val"], h["nonop_inc"]["val"] - h["nonop_exp"]["val"])
    chk("printed 22 = printed 20 + printed 21", L[22]["val"], L[20]["val"] + L[21]["val"])
    chk("printed 24 = printed 22 - printed 23 (tax sign by convention)", L[24]["val"], L[22]["val"] - L[23]["val"])
    chk("printed 31 = printed 24 + printed 25", L[31]["val"], L[24]["val"] + L[25]["val"])
    chk("printed 25 = sum of all printed OCI leaf rows (%s)" % "; ".join(x["label"].strip() for x in L["_leafs"]), L[25]["val"], L["_leaf_sum"])
    return out


def csm_status(q):
    b = d5[(CODE, q)]["csm"]
    return dict(status=b["status"], master_vector=b["now"], later_vector=b["latest"], pl4_eok=b.get("pl4_eok"))


gold_overlap = {q: [it for it in changed[q] if (CODE, it, q) in GOLD] for q in SPEC}
gold_in_block = {q: sorted(it for (c, it, qq) in GOLD if qq == q) for q in SPEC}

for q in SPEC:
    sp = SPEC[q]
    ids_before, ids_after, pc = closure(q, False), closure(q, True), printed_closure(LATER_VAL[q])
    ok_after = all(x.get("ok", True) for x in ids_after) and all(x["ok"] for x in pc)
    census_items = sorted(int(k) for k, v in d5[(CODE, q)]["its"].items() if v["master"] is not None and abs(v["prior"] - v["master"]) > 1e-3)
    csm_ok = d5[(CODE, q)]["csm"]["status"] == "SAME"
    adopt = bool(sp["approved"] and ok_after and not gold_overlap[q] and csm_ok)
    if not sp["approved"]:
        reason = ("outside the approved list (stays at the old vintage): owner gold cells in the block %s, item(s) %s would change; the stored gold holds the original-vintage values (2023.1Q/2Q reports), the later print is a different vintage" % (gold_in_block[q], gold_overlap[q]))
    elif adopt:
        reason = ("closes on the merged vector (20=1+17, |22-24|=|23|, 31=24+25, 25=sum of OCI parts, 17=18+19, LOB bridge 1 = 2+13+14+15-16 with master Tier-2 legs); no owner gold cell in the block; "
                  "CSM latest = master (SAME), PL4/CSM5 pair untouched; only 1/16/17/18 move (+18.852 / -18.852 / -18.852 / -18.852 eok), 20/22/23/24/25-32 are equal to the won")
    else:
        reason = "NOT CLOSED or gold overlap or CSM differs -- see closure lists"
    b = dict(
        quarter=q, adopt=adopt, approved_by_owner=sp["approved"], n_cells=len(changed[q]) if sp["approved"] else 0, items=changed[q] if sp["approved"] else [],
        items_that_differ_from_later_print=changed[q], items_equal_to_later_print=equal_items[q],
        later_filing=dict(fy=sp["later"][0], rcept=RCEPT[sp["later"][0]], file=stmt(sp["later"][0]).rel, statement_title_line=stmt(sp["later"][0]).title,
                          parent_section=stmt(sp["later"][0]).parent, unit=stmt(sp["later"][0]).unit, cumulative_column_position=sp["later"][1] + 1, three_month_column_position=sp["later"][2] + 1),
        census_items=census_items, items_equal_to_census=(census_items == changed[q]),
        gold_cells_in_block=gold_in_block[q], gold_overlap_with_changed_items=gold_overlap[q],
        user_pl_confirmed_cells_mentions_of_code=CONF_N,
        closure_master_before=ids_before, closure_merged_after=ids_after, closure_printed_later_filing=pc,
        csm=csm_status(q), csm_vs_master=d5[(CODE, q)]["csm"]["status"], reason=reason)
    if "orig" in sp:
        b["original_filing"] = dict(fy=sp["orig"][0], rcept=RCEPT[sp["orig"][0]], file=stmt(sp["orig"][0]).rel, statement_title_line=stmt(sp["orig"][0]).title, parent_section=stmt(sp["orig"][0]).parent, unit=stmt(sp["orig"][0]).unit)
    buckets.append(b)


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
FYQ = [f"2023.{n}Q" for n in (1, 2, 3, 4)]
model_mismatch, seam_cells, neighbour_effects, auto_follow = [], [], [], []

# model check over ALL items of FY2023/FY2024: derived(YTD master) == live 값_당분기 (so that the derivation rule used below is the production one)
for item in range(1, 33):
    for fy in ("2023", "2024"):
        qs = [f"{fy}.{n}Q" for n in (1, 2, 3, 4)]
        ytd = {q: mval(item, q) for q in qs}
        for q in qs:
            dm, dl = derived(ytd, q), mdangi(item, q)
            if (dm is None) != (dl is None) or (dm is not None and abs(dm - dl) > 1e-5):
                model_mismatch.append((item, q, dm, dl))

# later filings' annual 2023 print (FY2024_Q4 prior column) and original annual print (FY2023_Q4)
A_ORIG = read_items(stmt("FY2023_Q4"), 0, 3)
A_LATER = read_items(stmt("FY2024_Q4"), 1, 3, want_ctx="PFY2023dFY")
for fy in ("FY2023_Q4", "FY2024_Q4"):
    if stmt(fy).unit != "원":
        warnings.append(f"{fy}: unit {stmt(fy).unit}")
q4_status = {}
for it in CHECK_ITEMS:
    m = mval(it, "2023.4Q")
    if m is None:
        continue
    q4_status[it] = dict(master=m, orig_annual_print=round(A_ORIG[it]["val"], 6), fy2024_annual_prior_print=round(A_LATER[it]["val"], 6),
                         master_eq_orig=abs(m - A_ORIG[it]["val"]) <= TOL_WON, master_eq_later=abs(m - A_LATER[it]["val"]) <= TOL_WON,
                         xml_line_orig=A_ORIG[it]["parts"][0]["line"], xml_line_later=A_LATER[it]["parts"][0]["line"])
q4_all_equal_later = all(v["master_eq_later"] for v in q4_status.values())


def src_for_3m(q, item):
    sp = SPEC[q]
    rel = stmt(sp["later"][0]).rel
    p3 = LATER_3M[q][item]
    parts = p3["parts"]
    if len(parts) == 1:
        return f"{rel}:L{parts[0]['line']} [{parts[0]['label']}] {parts[0]['printed']}원"
    if item == 18:
        pp = {x["label"]: x for x in parts}
        t = parts[0]
        return (f"{rel}:L{t['line']} [{t['label']}] {t['printed']}원 (derived: item17 - item19; item19 = "
                + " ".join(f"{'+' if x['label'].endswith('수익') else '-'} L{x['line']} [{x['label']}] {x['printed']}원" for x in parts[1:])
                + "; in the 2024 filings the 비용 lines are printed positive)")
    return " || ".join(f"{rel}:L{p['line']} [{p['label']}] {p['printed']}원" + ("" if p["contribution_mn"] >= 0 else " (contribution %+.6f)" % p["contribution_mn"]) for p in parts)


def cls_of(item, q):
    b = d5.get((CODE, q))
    return None if b is None else b["cls"].get(str(item))


for item in POLICY_ITEMS:
    ytd_b = {q: mval(item, q) for q in FYQ}
    ytd_a = {q: adopted_new.get((item, q), mval(item, q)) for q in FYQ}
    for q in FYQ:
        n = int(q[5])
        db_live, da = mdangi(item, q), derived(ytd_a, q)
        cur_changed = (item, q) in adopted_new
        pq = f"2023.{n-1}Q" if n > 1 else None
        prev_changed = n > 1 and (item, pq) in adopted_new
        rec = dict(quarter=q, item=item, item_name=ITEM_NAME[item], old=db_live, derived_after_adoption=da,
                   operand_cur=dict(q=q, ytd_before=ytd_b[q], ytd_after=ytd_a[q], adopted=cur_changed),
                   operand_prev=(None if pq is None else dict(q=pq, ytd_before=ytd_b[pq], ytd_after=ytd_a[pq], adopted=prev_changed)))
        if n == 1 or (not cur_changed and not prev_changed):
            rec["class"] = "unchanged_both_old" if n > 1 else "q1_equals_ytd_unchanged"
            rec["why"] = "single quarter = YTD of Q1 (not adopted)" if n == 1 else "both YTD operands stay at the old vintage, nothing changes"
            neighbour_effects.append(rec)
        elif cur_changed and not prev_changed:
            # 2023.3Q: 9M adopted, 6M stays old (gold, not approved) -> seam; the later filing prints the restated 3-month column
            p3 = LATER_3M[q][item]
            new3 = round(p3["val"], 6)
            later_cum = LATER_VAL[q][item]["val"]
            sp = SPEC[q]
            # cross-check 1: 3M print = later 9M - 6M printed in the FY2024 Q2 report (prior column, new vintage)
            l6 = LATER_VAL["2023.2Q"][item]["val"]
            rec["class"] = "seam"
            rec["proposed"] = "set_dangi"
            rec["proposed_value"] = new3
            rec["three_month_print"] = dict(value=new3, xml_file=stmt(sp["later"][0]).rel, xml_rcept=RCEPT[sp["later"][0]],
                                            xml_period_column="prior-year 3-month column (2023.7.1-9.30) of the separate/OFS 4-2 statement, position 3 of 4",
                                            xml_lines=[dict(label=p["label"], line=p["line"], printed=p["printed"], contribution_mn=p["contribution_mn"]) for p in p3["parts"]],
                                            derivation=("direct print" if len(p3["parts"]) == 1 else "sum of printed lines (contributions in xml_lines)"))
            rec["cross_check_9M_minus_6M_both_new_vintage"] = dict(
                later_9M_prior_cum=round(later_cum, 6), fy2024_q2_report_6M_prior_cum=round(l6, 6), difference=round(later_cum - l6, 6), diff_vs_3m_print=round(later_cum - l6 - new3, 6),
                ok=abs(later_cum - l6 - new3) <= TOL_ID, fy2024_q2_line=LATER_VAL["2023.2Q"][item]["parts"][0]["line"], fy2024_q2_file=stmt("FY2024_Q2").rel)
            rec["old_derived_mixed_vintage"] = round(later_cum - ytd_b[pq], 6)       # new 9M - old 6M (what build_pl would produce without the fix)
            rec["set_dangi_cell"] = [CODE, q, item, new3, src_for_3m(q, item)]
            rec["reason"] = ("9M adopted (later vintage), 6M (2023.2Q) stays at the old vintage (owner gold cells 1/16/17/18/19, outside the approved list) -> build_pl would subtract two vintages; "
                             "the FY2024 Q3 report prints the restated 3-month column -> single quarter = printed 3-month value")
            seam_cells.append(rec)
        elif prev_changed and not cur_changed:
            lat_eq = q4_status.get(item, {}).get("master_eq_later")
            rec["class"] = "consistent_after_adoption" if lat_eq else "seam_unresolved"
            rec["why"] = ("annual 2023 (master = FY2023 annual print = FY2024 annual prior print) is already at the later vintage; 9M adopted now at the later vintage -> annual - 9M has both operands at the same vintage "
                          "(before adoption it mixed the later-vintage annual with the old 9M)" if lat_eq else "annual differs from the later annual print")
            rec["annual_checks"] = dict(master_annual=ytd_b[q], fy2023_annual_print=q4_status[item]["orig_annual_print"], fy2024_annual_prior_print=q4_status[item]["fy2024_annual_prior_print"],
                                        xml_line_orig=q4_status[item]["xml_line_orig"], xml_line_later=q4_status[item]["xml_line_later"])
            auto_follow.append(rec)
        else:
            rec["class"] = "other"
            neighbour_effects.append(rec)

# 3-month print vs live single quarter of the UNCHANGED items (3Q): confirms that the old vintage single quarter of the other items equals the printed 3M
unch_3m = []
q = "2023.3Q"
for item in CHECK_ITEMS:
    if item in POLICY_ITEMS:
        continue
    live = mdangi(item, q)
    if live is None:
        continue
    p3 = LATER_3M[q][item]["val"]
    unch_3m.append(dict(quarter=q, item=item, live_dangi=live, printed_3m_later=round(p3, 6), diff=round(live - p3, 6), ok=abs(live - p3) <= TOL_ID))
# original filing 3M print vs live single of the unchanged items (second look) and of the policy items (old vintage single = old 3M print?)
orig3_vs_live = []
for item in CHECK_ITEMS:
    live = mdangi(item, q)
    if live is None:
        continue
    p3 = ORIG_3M[q][item]["val"]
    orig3_vs_live.append(dict(item=item, live_dangi=live, orig_printed_3m=round(p3, 6), diff=round(live - p3, 6), ok=abs(live - p3) <= TOL_ID))

# single-quarter vector of 2023.3Q after the set_dangi fix: closure
hyb = {item: mdangi(item, "2023.3Q") for item in range(1, 33)}
for s in seam_cells:
    hyb[s["item"]] = s["proposed_value"]
hyb_close = []


def hchk(n, a, b):
    if a is None or b is None:
        hyb_close.append(dict(name=n, status="SKIP (operand empty)"))
        return
    hyb_close.append(dict(name=n, lhs=round(a, 6), rhs=round(b, 6), resid=round(a - b, 6), tol=TOL_ID, ok=abs(a - b) <= TOL_ID))


hchk("20 = 1 + 17", hyb[20], hyb[1] + hyb[17])
hchk("22 = 20 + 21", hyb[22], hyb[20] + hyb[21])
hchk("24 = 22 - 23", hyb[24], hyb[22] - hyb[23])
hchk("17 = 18 + 19", hyb[17], hyb[18] + hyb[19])
hchk("1 (single) = 2+13+14+15-16 (live Tier-2 singles)", hyb[1], sum((hyb[i] or 0) for i in (2, 13, 14, 15)) - hyb[16])
hchk("3M print: 20 = 1 + 17 (printed in the later filing)", LATER_3M["2023.3Q"][20]["val"], LATER_3M["2023.3Q"][1]["val"] + LATER_3M["2023.3Q"][17]["val"])

# 4Q single quarter before / after for ALL policy items and closure of the 4Q single vector after
q4_single = {}
v4b = {i: mdangi(i, "2023.4Q") for i in range(1, 33)}
v4a = dict(v4b)
for item in POLICY_ITEMS:
    ya = {q: adopted_new.get((item, q), mval(item, q)) for q in FYQ}
    v4a[item] = derived(ya, "2023.4Q")
    q4_single[item] = dict(live_dangi=v4b[item], derived_after_adoption=v4a[item], change=round(v4a[item] - v4b[item], 6), ytd4_master=mval(item, "2023.4Q"), ytd3_master=mval(item, "2023.3Q"), ytd3_after=adopted_new[(item, "2023.3Q")])
q4_close = {}
for tag, v in (("before", v4b), ("after", v4a)):
    cl = []
    for n, a, b in (("20 = 1 + 17", v[20], v[1] + v[17]), ("17 = 18 + 19", v[17], v[18] + v[19]),
                    ("1 = 2+13+14+15-16", v[1], sum((v[i] or 0) for i in (2, 13, 14, 15)) - v[16])):
        cl.append(dict(name=n, resid=round(a - b, 6), ok=abs(a - b) <= TOL_ID))
    q4_close[tag] = cl

# year tie 2023 for the policy items: sum of the four singles after adoption (1Q, 2Q old; 3Q set_dangi; 4Q derived) vs the annual master
tie = {}
for item in POLICY_ITEMS:
    s1 = mval(item, "2023.1Q")
    s2 = mval(item, "2023.2Q") - mval(item, "2023.1Q")
    s3 = [x for x in seam_cells if x["item"] == item][0]["proposed_value"]
    s4 = v4a[item]
    tot = s1 + s2 + s3 + s4
    tie[item] = dict(sum_of_four_singles_after=round(tot, 6), master_annual_2023_4Q=mval(item, "2023.4Q"), gap_vs_master_annual=round(tot - mval(item, "2023.4Q"), 6),
                     gap_equals_6M_old_minus_6M_later=round(mval(item, "2023.2Q") - LATER_VAL["2023.2Q"][item]["val"], 6),
                     before_adoption_sum_of_four_live_singles=round(sum(mdangi(item, q) for q in FYQ), 6))

# 2023.1Q / 2023.2Q facts (stay old)
stale_neighbours = {}
for q in ("2023.1Q", "2023.2Q"):
    stale_neighbours[q] = dict(items_differing_from_later_print=changed[q], gold_cells_in_block=gold_in_block[q], gold_overlap=gold_overlap[q],
                               rows=[dict(item=it, master=mval(it, q), later_print=round(LATER_VAL[q][it]["val"], 6), delta=round(LATER_VAL[q][it]["val"] - mval(it, q), 6), xml_line=LATER_VAL[q][it]["parts"][0]["line"],
                                          gold=((CODE, it, q) in GOLD), gold_was=(GOLD[(CODE, it, q)].get("was") if (CODE, it, q) in GOLD else None)) for it in changed[q]],
                               later_file=stmt(SPEC[q]["later"][0]).rel)

# lines that feed the Tier-2 legs (items 2..14 come from the notes built on these) are identical in the original and the later print; only the 기타사업비용 / 보험서비스비용 / 투자영업비용 lines move
leg_lines = {}
for key in ("ins_rev", "reins_rev", "ins_cost", "reins_cost", "inv_rev", "svc", "inv_cost"):
    o, l = ORIG_VAL["2023.3Q"]["_h"][key], LATER_VAL["2023.3Q"]["_h"][key]
    leg_lines[key] = dict(label=o["label"], orig_mn=round(o["val"], 6), later_mn=round(l["val"], 6), delta=round(l["val"] - o["val"], 6), line_orig=o["line"], line_later=l["line"])
pre_seam = [x for x in orig3_vs_live if not x["ok"]]
csm_cells = {}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    csm_cells[q] = {str(r["항목번호"]): r["값"] for r in csm_rows if r["공시분기"] == q}

verification = dict(
    master_equals_original_print_all=all(abs(mval(it, "2023.3Q") - ORIG_VAL["2023.3Q"][it]["val"]) <= TOL_WON for it in CHECK_ITEMS if mval(it, "2023.3Q") is not None),
    warnings=warnings, dangi_model_mismatch_vs_live_master=model_mismatch,
    census_vs_xml=dict(n_cells=len(cells), max_abs_diff=max(abs(c["second_source"]["fsapi"]["diff_vs_xml"]) for c in cells),
                       items_equal_to_census=[b["items_equal_to_census"] for b in buckets if b["quarter"] == "2023.3Q"],
                       candidate_cells_in_cand_pl_cells=len(cand), candidate_max_abs_diff_vs_xml=max(abs(c["census_candidate_diff_vs_xml"]) for c in cells if c["census_candidate_diff_vs_xml"] is not None)),
    alt_path=dict(n=len([c for c in cells if c["second_source"]["alt_path"]]), n_ok=len([c for c in cells if c["second_source"]["alt_path"] and c["second_source"]["alt_path"]["ok"]])),
    gold=dict(KR0082_gold_set_cells=len(GOLD), KR0082_gold_set_keys=sorted([list(k) for k in GOLD]), adopted_cells_hitting_gold=[(c["quarter"], c["item"]) for c in cells if c["gold_cell"]],
              user_pl_confirmed_cells_mentions_of_KR0082=CONF_N, null_dangi_existing=sorted(NULL_D), set_dangi_existing=sorted(SET_D),
              set_dangi_proposed_hitting_existing_null_or_set=[(s["quarter"], s["item"]) for s in seam_cells if (CODE, s["quarter"], s["item"]) in NULL_D or (CODE, s["quarter"], s["item"]) in SET_D]),
    seam_3m_vs_9M_minus_6M=dict(n=len(seam_cells), n_ok=sum(1 for s in seam_cells if s["cross_check_9M_minus_6M_both_new_vintage"]["ok"])),
    unchanged_items_3m_later_print_vs_live_single_2023_3Q=dict(n=len(unch_3m), n_ok=sum(1 for x in unch_3m if x["ok"]), not_ok=[x for x in unch_3m if not x["ok"]]),
    original_3m_print_vs_live_single_2023_3Q=dict(n=len(orig3_vs_live), n_ok=sum(1 for x in orig3_vs_live if x["ok"]), not_ok=[x for x in orig3_vs_live if not x["ok"]]),
    hybrid_single_2023_3Q_closure=hyb_close,
    tier2_proxy_printed_lines_orig_vs_later_9M=leg_lines,
    pre_existing_seam_in_old_vintage=dict(
        note=("the live 2023.3Q single quarter of items 1/16/17/18 (9M original - 6M gold from the half-year report) already differs by 189.389994 from the 3-month value printed in the ORIGINAL Q3 filing: "
              "the Q3 2023 report implies a 6M of 59,529.92 for item 1 while the half-year report (gold) printed 59,719.31; so three vintages exist (H1 original, Q3 original, FY2024 comparatives); the set_dangi cells replace this single quarter by the FY2024 Q3 3-month print"),
        rows=pre_seam),
    q2023_4Q=dict(status=q4_status, all_items_master_equals_fy2024_annual_prior_print=q4_all_equal_later, single_quarter=q4_single, single_quarter_closure=q4_close),
    year_tie_2023=tie,
    stale_neighbours=stale_neighbours,
    csm_waterfall_master_cells_unchanged=csm_cells,
)
plan = dict(code=CODE, company=NAME, generated="2026-10-22", source_tool="data/_derived/remaining_20261022/e19_latest_comparative/KR0082_plan.py", master_unit="백만원",
            statement="separate (OFS) 4-2. 포괄손익계산서 (section 4. 재무제표), prior-year cumulative column of the next-year Q3 report", buckets=buckets, cells=cells,
            seam_cells=seam_cells, neighbour_effects=neighbour_effects, auto_follow_cells=auto_follow, verification=verification)
plan["apply_contract"] = dict(
    gold_set_cells=[[CODE, c["item"], c["quarter"], c["new"], c["old"]] for c in cells],
    gold_set_notes={f"{c['quarter']}|{c['item']}": c["gold_note"] for c in cells},
    null_dangi_cells=[],
    set_dangi_cells=[s["set_dangi_cell"] for s in seam_cells],
    expected_master_changes=dict(
        value_cells_changed=len(cells),
        dangi_cells_set_by_set_dangi=len(seam_cells),
        dangi_cells_auto_follow_2023_4Q=[(a["quarter"], a["item"], a["old"], a["derived_after_adoption"]) for a in auto_follow],
        dangi_cells_2023_1Q_2Q_2024_and_later="unchanged"),
    do_not_touch=dict(owner_gold_cells=sorted([list(k) for k in GOLD]), csm_waterfall="unchanged for 2023.3Q (census SAME; item 4 differs by 0.1 eok only in the rounded later vector)",
                      items_not_in_cells="all other items incl. 19, 20-32 (equal to the later print to the won)",
                      buckets_not_adopted="2023.1Q and 2023.2Q (owner gold 1/16/17/18/19, outside the approved list), 2023.4Q (master already equals the FY2024 annual prior print)"),
    census_note="GOLD_OVERLAY_CENSUS PL tuple: user_pl_cells.json set +%d (KR0082 2023.3Q items 1,16,17,18) and set_dangi.cells +%d (KR0082 2023.3Q items 1,16,17,18); null_dangi +0" % (len(cells), len(seam_cells)),
    gate_notes="adopt 2023.3Q together with the 4 set_dangi cells: otherwise build_pl derives 2023.3Q single = new 9M - old 6M (mixed vintage); the 2023.4Q single (annual - 9M) moves to a consistent vector automatically")
(HERE / "plan_KR0082.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

L = []
for b in buckets:
    L.append(f"== {b['quarter']} adopt={b['adopt']} approved={b['approved_by_owner']} cells={b['n_cells']} items={b['items']} differ_from_later={b['items_that_differ_from_later_print']} equal_items={b['items_equal_to_later_print']} census_items_equal={b['items_equal_to_census']} gold_in_block={b['gold_cells_in_block']} overlap={b['gold_overlap_with_changed_items']} csm={b['csm_vs_master']}")
    L.append(f"   later {b['later_filing']['fy']} rcept {b['later_filing']['rcept']} unit {b['later_filing']['unit']} title L{b['later_filing']['statement_title_line']} parent {b['later_filing']['parent_section']}  reason: {b['reason']}")
    for k in ("closure_master_before", "closure_merged_after", "closure_printed_later_filing"):
        L.append(f"   {k}:")
        for x in b[k]:
            L.append(f"      {x.get('name')}: " + ("SKIP" if ('resid' not in x and 'resids' not in x) else (f"resids={x['resids']} ok={x['ok']}" if 'resids' in x else f"resid={x['resid']} tol={x['tol']} ok={x['ok']}")))
L.append("")
for c in cells:
    ap = c["second_source"]["alt_path"]
    L.append(f"CELL {c['quarter']} i{c['item']:>2} {c['item_name']}: old={c['old']} new={c['new']} delta={c['delta']} L{c['xml_line']} fsapi_diff={c['second_source']['fsapi']['diff_vs_xml']} cand_diff={c['census_candidate_diff_vs_xml']} alt={'-' if ap is None else (ap['value'], ap['diff_vs_xml'], ap['ok'])} mastEqOrig={c['master_equals_original_print']} deriv={c['derivation']} lines={[(x['label'], x['line'], x['printed']) for x in c['xml_lines']]}")
L.append("")
L.append(f"SEAM ({len(seam_cells)}):")
for s in seam_cells:
    L.append(f"   {s['quarter']} i{s['item']} old={s['old']} derived_mixed={s['old_derived_mixed_vintage']} -> {s['proposed']} {s['proposed_value']} 9M-6M check ok={s['cross_check_9M_minus_6M_both_new_vintage']['ok']} (diff {s['cross_check_9M_minus_6M_both_new_vintage']['diff_vs_3m_print']}) line={[(x['label'], x['line'], x['printed']) for x in s['three_month_print']['xml_lines']]}")
L.append(f"AUTO_FOLLOW ({len(auto_follow)}):")
for s in auto_follow:
    L.append(f"   {s['quarter']} i{s['item']} {s['class']} old={s['old']} after={s['derived_after_adoption']} annual_checks={s['annual_checks']}")
L.append(f"NEIGHBOUR unchanged ({len(neighbour_effects)}):")
for s in neighbour_effects:
    L.append(f"   {s['quarter']} i{s['item']} class={s['class']} old={s['old']} after={s['derived_after_adoption']}")
L.append("VERIFICATION " + json.dumps({k: v for k, v in verification.items() if k not in ('q2023_4Q', 'csm_waterfall_master_cells_unchanged', 'year_tie_2023', 'stale_neighbours')}, ensure_ascii=False, default=str))
L.append("2023.4Q status (master vs annual prints):")
for k, v in q4_status.items():
    L.append(f"   i{k} " + json.dumps(v, ensure_ascii=False))
L.append("2023.4Q single quarter:")
for k, v in q4_single.items():
    L.append(f"   i{k} " + json.dumps(v, ensure_ascii=False))
L.append("2023.4Q single closure: " + json.dumps(q4_close, ensure_ascii=False))
L.append("year tie 2023:")
for k, v in tie.items():
    L.append(f"   i{k} " + json.dumps(v, ensure_ascii=False))
L.append("stale neighbours:")
for k, v in stale_neighbours.items():
    L.append(f"   {k} " + json.dumps(v, ensure_ascii=False))
(HERE / "KR0082_plan_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
print("done", len(cells), len(seam_cells), len(neighbour_effects), len(auto_follow), len(warnings), len(model_mismatch))
