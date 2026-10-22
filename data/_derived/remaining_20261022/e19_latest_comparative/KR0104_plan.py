# -*- coding: utf-8 -*-
"""KR0104 (NH Life) latest-comparative adoption plan for bucket 2023.3Q -- READ-ONLY on every master / gold / doc.
Independent re-read (own XML reader KR0104_xml.py, no scripts/ or src/ readers) of the SEPARATE-basis statement of comprehensive income
('4-2. 포괄손익계산서', section '4. 재무제표') of
  * the original filing   FY2023_Q3 (rcept 20231114001637, unit 백만원), cumulative current column      -> proves master = original print
  * the later filing      FY2024_Q3 (rcept 20241114000851, unit 원),     prior-year cumulative column   -> adoption values; prior-year 3-month column -> set_dangi
  * neighbours            FY2024_Q1 / FY2024_Q2 prior columns (2023.1Q / 2023.2Q, not approved), FY2023_Q4 / FY2024_Q4 (2023.4Q annual)
  * the restatement note  FY2024_Q3 L25325.. (effect table 수정 전 / 수정금액 / 수정 후) as a third source
Closure on the merged vector (gate function validate_master_tables._check_pl_bridge + explicit identities), single quarter (값_당분기) seam analysis, year tie.
Writes plan_KR0104.json + KR0104_plan_report.txt next to this script.  python = C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"""
import json, os, re, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import KR0104_xml as X
ROOT = X.ROOT
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import validate_master_tables as V          # gate code (read-only use of _check_pl_bridge / norm)

CODE, NAME = "KR0104", "농협생명"
TOL_WON = 2e-5          # equality tolerance (mn) for won-precise prints
TOL_ID = 0.002          # identity tolerance (mn) for won-precise vectors
BAND = 1.5              # print-rounding band (mn) of a 백만원 print: +-0.5 rounding, up to +-1 footing plug per line

ITEM_NAME = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익",
             25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익",
             30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}
CHECK_ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
CENSUS_ITEMS = [17, 18, 20, 22, 23, 24, 28, 31]          # ticket / census list for KR0104 2023.3Q

RCEPT = {"FY2023_Q1": "20230515002904", "FY2023_Q2": "20230814001979", "FY2023_Q3": "20231114001637", "FY2023_Q4": "20240401002122",
         "FY2024_Q1": "20240514001371", "FY2024_Q2": "20240814002115", "FY2024_Q3": "20241114000851", "FY2024_Q4": "20250331003065"}
# later = (filing, position of the prior-year CUMULATIVE value, position of the prior-year 3-MONTH value, number of numeric cells)
SPEC = {
    "2023.1Q": dict(later=("FY2024_Q1", 3, 2, 4), approved=False),
    "2023.2Q": dict(later=("FY2024_Q2", 3, 2, 4), approved=False),
    "2023.3Q": dict(orig=("FY2023_Q3", 1, 4), orig3m=("FY2023_Q3", 0, 4), later=("FY2024_Q3", 3, 2, 4), approved=True),
}
APPROVED = [q for q, s in SPEC.items() if s["approved"]]
HAS_LETTER = re.compile(r"[가-힣A-Za-z]")


def norm(label):
    s = (label or "").replace("\u3000", "").replace(" ", "")
    s = re.sub(r"^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]|[IVX]+)\.", "", s)
    s = re.sub(r"\(주[^)]*\)", "", s)
    s = s.replace("(손실)", "").replace("(수익)", "")
    return s


def cellval(c):
    if c["val"] is not None:
        return c["val"]
    if c["text"].strip() == "-":
        return 0.0
    raise RuntimeError(f"value not numeric: {c['text']!r}")


class Stmt:
    def __init__(self, fy):
        self.fy = fy
        self.title, self.end, rows = X.read_statement(fy)
        self.rel = X.FILES[fy]
        self.rows = []
        in_oci, sect = False, None
        unit = "?"
        for r in rows:
            lab_text, lab_line = r["label"] if r["label"] else ("", None)
            lab = norm(lab_text)
            if unit == "?" and "단위" in lab_text:
                unit = "백만원" if "백만원" in lab_text else ("원" if "원" in lab_text else "?")
            cells = [c for c in r["cells"] if c["text"] != ""]
            sub = False
            if lab == "기타포괄손익":
                in_oci, sect = True, None
            if in_oci and lab.startswith("후속적으로당기손익으로재분류되지않는"):
                sect, sub = "N", True
            elif in_oci and lab.startswith("후속적으로당기손익으로재분류될수있는"):
                sect, sub = "R", True
            self.rows.append(dict(raw=lab_text, lab=lab, line=lab_line, tr=r["tr_line"], cells=cells, sect=sect if in_oci else None, oci=in_oci, subtotal=sub))
            if lab.endswith("총포괄손익") and lab == "총포괄손익":
                in_oci = False
        self.unit = unit
        self.scale = 1e6 if unit == "원" else 1.0
        lines = X.load_lines(fy)
        self.parent = None
        for i in range(self.title - 1, 0, -1):
            if lines[i - 1].startswith("<TITLE") and re.search(r">\s*\d\. [^<]*재무제표[^<]*<", lines[i - 1]) and "-" not in re.sub(r"<[^>]+>", "", lines[i - 1])[:4]:
                self.parent = (i, re.sub(r"<[^>]+>", "", lines[i - 1]).strip())
                break

    def pick(self, names, pos, nc, want_ctx=None, sect=None, optional=False):
        cand = [r for r in self.rows if r["lab"] in names and not r["subtotal"] and (sect is None or r["sect"] == sect) and len(r["cells"]) == nc]
        if not cand:
            if optional:
                return None
            raise KeyError(f"{self.fy}: none of {names} (sect={sect}, nc={nc})")
        if len(cand) > 1:
            raise RuntimeError(f"{self.fy}: ambiguous {names}: {[(c['raw'], c['line']) for c in cand]}")
        r = cand[0]
        if want_ctx:
            cs = [c for c in r["cells"] if c["ctx"].startswith(want_ctx + "_") and "SeparateMember" in c["ctx"]]
            if len(cs) != 1:
                raise RuntimeError(f"{self.fy}: {r['raw']}: ctx {want_ctx} separate -> {len(cs)} cells")
            c = cs[0]
        else:
            c = r["cells"][pos]
        return dict(printed=cellval(c), raw=c["text"], line=c["line"], label=r["raw"].replace("\u3000", " ").strip(), ctx=c["ctx"])

    def oci_leafs(self, pos, nc, want_ctx=None):
        out = []
        for r in self.rows:
            if r["oci"] and not r["subtotal"] and r["lab"] not in ("기타포괄손익", "총포괄손익") and len(r["cells"]) == nc:
                if want_ctx:
                    cs = [c for c in r["cells"] if c["ctx"].startswith(want_ctx + "_") and "SeparateMember" in c["ctx"]]
                    c = cs[0]
                else:
                    c = r["cells"][pos]
                out.append(dict(label=r["raw"].strip(), printed=cellval(c), val=cellval(c) / self.scale, line=c["line"], raw=c["text"]))
        return out


def part(p, contribution_mn):
    return dict(label=p["label"], line=p["line"], printed=p["raw"], contribution_mn=round(contribution_mn, 6))


def read_items(st, pos, nc, want_ctx=None, helpers=True):
    """-> dict item -> dict(val (백만원, master sign convention), parts[...]) plus helper lines.  Both KR0104 vintages print expenses positive."""
    sc = st.scale

    def pk(names, sect=None, optional=False):
        return st.pick(names, pos, nc, want_ctx, sect, optional)

    out = {}
    ins_cost = pk(["보험영업비용"])
    if ins_cost["printed"] <= 0:
        raise RuntimeError(f"{st.fy}: 보험영업비용 not positive: expenses printed negative -> sign rule needed")

    def direct(it, names, sect=None):
        p = pk(names, sect)
        out[it] = dict(val=p["printed"] / sc, parts=[part(p, p["printed"] / sc)])

    for it, names in ((1, ["보험손익"]), (16, ["기타사업비용"]), (17, ["투자손익"]), (20, ["영업이익"]), (21, ["영업외손익"]), (22, ["법인세차감전순이익"]),
                      (23, ["법인세비용"]), (24, ["당기순이익", "분기순이익", "반기순이익"]), (25, ["기타포괄손익"]), (31, ["총포괄손익"])):
        direct(it, names)
    direct(26, ["기타포괄손익-공정가치측정금융자산관련손익"], "R")
    direct(29, ["기타포괄손익-공정가치측정금융자산평가손익"], "N")
    direct(27, ["보험계약자산(부채)순금융손익"])
    direct(28, ["현금흐름위험회피파생상품평가손익"], "R")
    direct(30, ["재보험계약자산(부채)순금융손익"])
    # 19 = (보험금융수익 + 재보험금융수익) - (보험금융비용 + 재보험금융비용); KR0104 statements carry only the two cost rows
    parts, v19 = [], 0.0
    for nm, sg, opt in (("보험금융수익", 1, True), ("재보험금융수익", 1, True), ("보험금융비용", -1, False), ("재보험금융비용", -1, False)):
        p = pk([nm], None, opt)
        if p is None:
            continue
        contrib = sg * p["printed"] / sc
        v19 += contrib
        parts.append(part(p, contrib))
    out[19] = dict(val=v19, parts=parts)
    out[18] = dict(val=out[17]["val"] - out[19]["val"], parts=[dict(out[17]["parts"][0])] + [dict(p, contribution_mn=-p["contribution_mn"]) for p in out[19]["parts"]])
    out[32] = dict(val=out[25]["val"] - sum(out[i]["val"] for i in (26, 27, 28, 29, 30)),
                   parts=[dict(out[25]["parts"][0])] + [dict(out[i]["parts"][0], contribution_mn=-out[i]["parts"][0]["contribution_mn"]) for i in (26, 27, 28, 29, 30)])
    if helpers:
        h = {}
        for key, names in (("rev_ins", ["보험영업수익"]), ("cost_ins", ["보험영업비용"]), ("inv_rev", ["투자영업수익"]), ("inv_cost", ["투자영업비용"]), ("nonop_inc", ["영업외수익"]), ("nonop_exp", ["영업외비용"]),
                           ("svc", ["보험서비스비용", "발행한보험계약에서생기는보험서비스비용"]), ("reins_cost", ["재보험비용"]), ("ins_rev", ["보험수익"]), ("reins_rev", ["재보험수익"])):
            p = pk(names)
            h[key] = dict(val=p["printed"] / sc, line=p["line"], raw=p["raw"], label=p["label"])
        out["_h"] = h
        leafs = st.oci_leafs(pos, nc, want_ctx)
        out["_leafs"] = leafs
        out["_leaf_sum"] = sum(x["val"] for x in leafs)
    return out


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


pl_rows = load_json("PL_breakdown.json")
M = defaultdict(dict)
NAMES_V = {}
for r in pl_rows:
    if r["원보험사코드"] == CODE:
        M[r["항목번호"]][r["공시분기"]] = r
        NAMES_V[r["항목번호"]] = V.norm(r["항목명"])
CO_NAME = [r["원수사명"] for r in pl_rows if r["원보험사코드"] == CODE][0]
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


warnings = []
cells, buckets = [], []
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
    exp_unit = {"FY2023_Q3": "백만원"}
    for fy in fys:
        want = exp_unit.get(fy, "원")
        if stmt(fy).unit != want:
            warnings.append(f"{fy}: unit {stmt(fy).unit} (expected {want})")

# ------------------------------------------------------------------ restatement note table (third source), FY2024_Q3 L25325..
NOTE_FILE = X.FILES["FY2024_Q3"]
_nl = X.load_lines("FY2024_Q3")
_P = re.compile(r"<P[^>]*>(.*?)</P>")
_TAG = re.compile(r"<[^>]+>")
note_texts = []
for i in range(25380, 25455):
    t = _TAG.sub("", _nl[i - 1]).replace("\u3000", " ").strip()
    if t:
        note_texts.append((i, t))
# layout after the 4 header cells ('과 목','2023년 3분기','수정 전','수정금액','수정 후'): label, before, delta, after
k0 = [j for j, (ln, t) in enumerate(note_texts) if t == "수정 후"][0] + 1
NOTE = {}
j = k0
while j + 3 < len(note_texts):
    lab = note_texts[j][1]
    NOTE[norm(lab)] = dict(label=lab, label_line=note_texts[j][0], before=note_texts[j + 1], delta=note_texts[j + 2], after=note_texts[j + 3])
    j += 4


def note_num(t):
    return 0.0 if t.strip() == "-" else X.num(t)


NOTE_ITEM = {1: "보험손익", 17: "투자손익", 20: "영업이익", 21: "영업외손익", 22: "법인세비용차감전순이익", 23: "법인세비용", 24: "분기순이익", 31: "분기총포괄손익"}
for it, lab in NOTE_ITEM.items():
    if norm(lab) not in NOTE:
        warnings.append(f"restatement note table: row {lab} not found")

# ------------------------------------------------------------------ changed items per bucket (later cumulative print vs master)
changed, equal_items, klass = {}, {}, {}
for q, sp in SPEC.items():
    ch, eq = [], []
    for it in CHECK_ITEMS:
        old = mval(it, q)
        if old is None:
            continue
        if "orig" in sp:
            org = ORIG_VAL[q][it]["val"]
            if abs(old - org) > 1e-6:
                warnings.append(f"{q} item {it}: master {old} != original print {org}")
        if abs(LATER_VAL[q][it]["val"] - old) > TOL_WON:
            ch.append(it)
        else:
            eq.append(it)
    changed[q], equal_items[q] = ch, eq
for it in changed["2023.3Q"]:
    klass[it] = "RESTATED" if abs(LATER_VAL["2023.3Q"][it]["val"] - mval(it, "2023.3Q")) > BAND else "PRINT_ROUNDING"


def alt_path(L, it):
    h = L["_h"]
    if it == 1:
        return h["rev_ins"]["val"] - h["cost_ins"]["val"], "보험영업수익 - 보험영업비용", [h["rev_ins"], h["cost_ins"]]
    if it == 16:
        return h["cost_ins"]["val"] - h["svc"]["val"] - h["reins_cost"]["val"], "보험영업비용 - 보험서비스비용 - 재보험비용", [h["cost_ins"], h["svc"], h["reins_cost"]]
    if it == 17:
        return h["inv_rev"]["val"] - h["inv_cost"]["val"], "투자영업수익 - 투자영업비용", [h["inv_rev"], h["inv_cost"]]
    if it == 18:
        fin = sum(p["contribution_mn"] for p in L[19]["parts"])        # negative (costs)
        return h["inv_rev"]["val"] - (h["inv_cost"]["val"] + fin), "투자영업수익 - (투자영업비용 - 보험금융비용 - 재보험금융비용)", [h["inv_rev"], h["inv_cost"]] + [dict(label=p["label"], line=p["line"], raw=p["printed"]) for p in L[19]["parts"]]
    if it == 20:
        return h["rev_ins"]["val"] - h["cost_ins"]["val"] + h["inv_rev"]["val"] - h["inv_cost"]["val"], "(보험영업수익-보험영업비용)+(투자영업수익-투자영업비용)", [h["rev_ins"], h["cost_ins"], h["inv_rev"], h["inv_cost"]]
    if it == 21:
        return h["nonop_inc"]["val"] - h["nonop_exp"]["val"], "영업외수익 - 영업외비용", [h["nonop_inc"], h["nonop_exp"]]
    if it == 22:
        return L[20]["val"] + L[21]["val"], "영업이익 + 영업외손익", [dict(label=L[20]["parts"][0]["label"], line=L[20]["parts"][0]["line"], raw=L[20]["parts"][0]["printed"]), dict(label=L[21]["parts"][0]["label"], line=L[21]["parts"][0]["line"], raw=L[21]["parts"][0]["printed"])]
    if it == 23:
        return L[22]["val"] - L[24]["val"], "법인세차감전순이익 - 분기순이익", [dict(label=L[22]["parts"][0]["label"], line=L[22]["parts"][0]["line"], raw=L[22]["parts"][0]["printed"]), dict(label=L[24]["parts"][0]["label"], line=L[24]["parts"][0]["line"], raw=L[24]["parts"][0]["printed"])]
    if it == 24:
        return L[22]["val"] - L[23]["val"], "법인세차감전순이익 - 법인세비용", [dict(label=L[22]["parts"][0]["label"], line=L[22]["parts"][0]["line"], raw=L[22]["parts"][0]["printed"]), dict(label=L[23]["parts"][0]["label"], line=L[23]["parts"][0]["line"], raw=L[23]["parts"][0]["printed"])]
    if it == 25:
        return L["_leaf_sum"], "기타포괄손익 하위 인쇄 줄 합계 (%s)" % "; ".join(x["label"] for x in L["_leafs"]), [dict(label=x["label"], line=x["line"], raw=x["raw"]) for x in L["_leafs"]]
    if it == 31:
        return L[24]["val"] + L[25]["val"], "당기순이익 + 기타포괄손익", [dict(label=L[24]["parts"][0]["label"], line=L[24]["parts"][0]["line"], raw=L[24]["parts"][0]["printed"]), dict(label=L[25]["parts"][0]["label"], line=L[25]["parts"][0]["line"], raw=L[25]["parts"][0]["printed"])]
    if it == 32:
        other = [x for x in L["_leafs"] if x["label"] not in ("기타포괄손익-공정가치측정금융자산관련손익", "기타포괄손익-공정가치측정금융자산평가손익", "현금흐름위험회피파생상품평가손익", "보험계약자산(부채)순금융손익", "재보험계약자산(부채)순금융손익")]
        return sum(x["val"] for x in other), "OCI 하위 줄 중 26/27/28/29/30 이외 줄 합계 (%s)" % "; ".join(x["label"] for x in other), [dict(label=x["label"], line=x["line"], raw=x["raw"]) for x in other]
    return None


def print_closure(L, tol):
    h = L["_h"]
    out = []

    def chk(n, a, b):
        out.append(dict(name=n, resid=round(a - b, 6), tol=tol, ok=abs(a - b) <= tol))

    chk("printed 보험영업수익 = 보험수익 + 재보험수익", h["rev_ins"]["val"], h["ins_rev"]["val"] + h["reins_rev"]["val"])
    chk("printed 보험손익 = 보험영업수익 - 보험영업비용", L[1]["val"], h["rev_ins"]["val"] - h["cost_ins"]["val"])
    chk("printed 보험영업비용 = 보험서비스비용 + 재보험비용 + 기타사업비용", h["cost_ins"]["val"], h["svc"]["val"] + h["reins_cost"]["val"] + L[16]["val"])
    chk("printed 투자손익 = 투자영업수익 - 투자영업비용", L[17]["val"], h["inv_rev"]["val"] - h["inv_cost"]["val"])
    chk("printed 20 = printed 1 + printed 17", L[20]["val"], L[1]["val"] + L[17]["val"])
    chk("printed 21 = 영업외수익 - 영업외비용", L[21]["val"], h["nonop_inc"]["val"] - h["nonop_exp"]["val"])
    chk("printed 22 = printed 20 + printed 21", L[22]["val"], L[20]["val"] + L[21]["val"])
    chk("printed 24 = printed 22 - printed 23", L[24]["val"], L[22]["val"] - L[23]["val"])
    chk("printed 31 = printed 24 + printed 25", L[31]["val"], L[24]["val"] + L[25]["val"])
    chk("printed 25 = sum of all printed OCI leaf rows", L[25]["val"], L["_leaf_sum"])
    chk("printed 17 = 18 + 19 (production definition)", L[17]["val"], L[18]["val"] + L[19]["val"])
    return out


# ------------------------------------------------------------------ cells (scope B: every item whose master value differs from the later print at won precision)
q3 = "2023.3Q"
sp3 = SPEC[q3]
sl3 = stmt(sp3["later"][0])
for it in changed[q3]:
    lat = LATER_VAL[q3][it]
    old = mval(it, q3)
    cn = d5[(CODE, q3)]["its"][str(it)]
    ap = alt_path(LATER_VAL[q3], it)
    ap_o = alt_path(ORIG_VAL[q3], it)
    ntitem = NOTE_ITEM.get(it)
    nrow = NOTE.get(norm(ntitem)) if ntitem else None
    oo = ORIG_VAL[q3][it]
    cells.append(dict(
        quarter=q3, item=it, item_name=ITEM_NAME[it], old=old, new=round(lat["val"], 6), delta=round(lat["val"] - old, 6), cls=klass[it], in_census_list=(it in CENSUS_ITEMS),
        unit="백만원", source_unit=sl3.unit, source_print="won (exact)",
        xml_file=sl3.rel, xml_rcept=RCEPT[sp3["later"][0]],
        xml_period_column="prior-year cumulative column (2023.1.1-9.30) of the separate/OFS 4-2 statement; 4 numeric cells [3M cur, cum cur, 3M prior, cum prior], position 4",
        xml_line=lat["parts"][0]["line"],
        xml_lines=[dict(label=p["label"], line=p["line"], printed=p["printed"], contribution_mn=p["contribution_mn"]) for p in lat["parts"]],
        derivation=("direct print" if len(lat["parts"]) == 1 else ("derived item 18 = item 17 - item 19 (production definition; contributions in xml_lines)" if it == 18 else
                    ("derived item 19 = -(보험금융비용 + 재보험금융비용) (no 수익 rows in the KR0104 statement)" if it == 19 else "derived item 32 = item 25 - (26+27+28+29+30) (production definition)"))),
        sign_note=("both vintages print expenses positive; master carries 기타사업비용/법인세 positive: contribution = printed; item 19 = -(finance costs) negative" if it in (16, 18, 19, 23) else None),
        second_source=dict(
            fsapi=dict(kind="DART FS-API frmtrm column of the same FY2024 Q3 filing (census d5_buckets.json prior)", value=cn["prior"], diff_vs_xml=round(cn["prior"] - lat["val"], 6)),
            alt_path=(None if ap is None else dict(kind="independent arithmetic path from other printed lines of the same column", formula=ap[1], value=round(ap[0], 6), diff_vs_xml=round(ap[0] - lat["val"], 6), ok=abs(ap[0] - lat["val"]) <= TOL_ID,
                                                   lines=[dict(label=x["label"], line=x["line"], printed=x.get("raw") or x.get("printed")) for x in ap[2]])),
            restatement_note=(None if nrow is None else dict(
                kind="FY2024 Q3 report restatement note table (전기오류 정정, 수정 전 / 수정금액 / 수정 후, unit 백만원, truncated to whole 백만원)", file=NOTE_FILE, label=nrow["label"],
                before=dict(value=note_num(nrow["before"][1]), line=nrow["before"][0]), delta=dict(value=note_num(nrow["delta"][1]), line=nrow["delta"][0]), after=dict(value=note_num(nrow["after"][1]), line=nrow["after"][0]),
                diff_after_vs_xml=round(note_num(nrow["after"][1]) - lat["val"], 6), within_print_band=abs(note_num(nrow["after"][1]) - lat["val"]) <= BAND,
                delta_vs_xml_minus_master=round(note_num(nrow["delta"][1]) - (lat["val"] - old), 6))),
        ),
        census_new=cn["prior"], census_master=cn["master"], census_candidate_new=(cand[(q3, it)][4] if (q3, it) in cand else None),
        census_candidate_diff_vs_xml=(round(cand[(q3, it)][4] - lat["val"], 6) if (q3, it) in cand else None),
        master_equals_original_print=abs(old - oo["val"]) <= 1e-6,
        original_print=dict(value=round(oo["val"], 6), xml_file=stmt(sp3["orig"][0]).rel, xml_line=oo["parts"][0]["line"], rcept=RCEPT[sp3["orig"][0]], unit="백만원",
                            xml_lines=[dict(label=p["label"], line=p["line"], printed=p["printed"], contribution_mn=p["contribution_mn"]) for p in oo["parts"]]),
        gold_cell=((CODE, it, q3) in GOLD)))

NOTE_CAUSE = ("후속 공시(FY2024 3분기보고서)가 전기오류(K-IFRS 제1109호 최초적용 시 일부 금융상품 분류 오류, 주석 '전기오류의 성격' %s L25325)를 정정해 재작성한 비교열이다"
              % X.FILES["FY2024_Q3"].split("/")[-1])
for c in cells:
    lf = SPEC[c["quarter"]]["later"]
    nt = c["second_source"]["restatement_note"]
    if c["cls"] == "RESTATED":
        cause = (f"변동 {c['delta']:+.6f}: {NOTE_CAUSE}. 정정 주석 표 수정 후 {nt['after']['value']:,.0f} (L{nt['after']['line']}, 수정금액 {nt['delta']['value']:,.0f} L{nt['delta']['line']})."
                 if nt else f"변동 {c['delta']:+.6f}: {NOTE_CAUSE} (파생 항목, 구성 줄의 변동에서 따라 움직임).")
    else:
        cause = (f"변동 {c['delta']:+.6f}: 재작성이 아니라 반올림 차이다. 원 공시는 백만원으로 반올림 인쇄({c['old']:,.0f})했고 후속 공시는 원 단위로 인쇄한 정밀값을 쓴다. "
                 + (f"정정 주석 표도 이 항목의 수정금액이 {nt['delta']['value']:,.0f}(L{nt['delta']['line']})이다. " if nt else "")
                 + "owner 규칙 '반올림 차이는 정밀한 쪽'에 따라 한 열의 값으로 맞춘다.")
    c["gold_note"] = (f"2026-10-22 parser/ifrs17 (KR0104 최신 비교열 채택, owner 결정 2026-10-22, 교보생명 선례와 동일): 별도(OFS) 기준 4-2 포괄손익계산서, {lf[0]} rcept {RCEPT[lf[0]]} 의 "
                      f"전기(2023.9.30 누적) 열 = {c['new']} 백만원. 원문 {c['xml_file']} L{c['xml_line']}" + ("" if c["derivation"] == "direct print" else " 외 합산 줄(xml_lines)") +
                      f". 단위 원(정확 인쇄). 현재 마스터값 {c['old']} 는 원 공시 FY2023_Q3 rcept {RCEPT['FY2023_Q3']}(단위 백만원) 인쇄값과 일치. {cause} "
                      f"2차 근거 FS-API frmtrm 일치 및 같은 열의 다른 인쇄 줄에 의한 독립 산식 일치. 증거 data/_derived/remaining_20261022/e19_latest_comparative/plan_KR0104.json")


# ------------------------------------------------------------------ closure
def merged_vec(q, items):
    v = {it: mval(it, q) for it in range(1, 33)}
    for c in cells:
        if c["quarter"] == q and c["item"] in items:
            v[c["item"]] = c["new"]
    return v


def closure(q, items, tol):
    v = merged_vec(q, items)
    res = []

    def chk(name, lhs, rhs, note=None):
        if lhs is None or rhs is None:
            res.append(dict(name=name, status="SKIP (operand empty)"))
            return
        d = lhs - rhs
        r = dict(name=name, lhs=round(lhs, 6), rhs=round(rhs, 6), resid=round(d, 6), tol=tol, ok=abs(d) <= tol)
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
    res.append(dict(name="I7 Tier-2 tree (informational, unchanged by adoption)", resids=t2, ok=all(abs(x) <= tol for x in t2.values())))
    return res


def gate(q, items):
    """production gate code (validate_master_tables._check_pl_bridge, source_ids={} = strict) on the merged vector"""
    v = merged_vec(q, items)
    m = {NAMES_V[k]: v[k] for k in NAMES_V}
    r = V._check_pl_bridge({(CO_NAME, q): m}, None, [], None, {}, None)
    return dict(passed=r[0], fail=[list(x) for x in r[1]], skip=r[2])


ALL18 = set(changed[q3])
SCOPES = {"B_all_differing_items": ALL18, "A_census_8": set(CENSUS_ITEMS) & ALL18, "A_restated_only": {i for i in ALL18 if klass[i] == "RESTATED"}}
scope_closure = {}
for nm, its in SCOPES.items():
    cl = closure(q3, its, BAND)
    scope_closure[nm] = dict(items=sorted(its), n=len(its), gate=gate(q3, its),
                             identities=[{k: x[k] for k in ("name", "resid", "ok") if k in x} for x in cl if "resid" in x],
                             worst_abs_resid=max(abs(x["resid"]) for x in cl if "resid" in x), tier2_ok=[x for x in cl if x["name"].startswith("I7")][0]["ok"])
scope_closure["master_before"] = dict(items=[], n=0, gate=gate(q3, set()), identities=[{k: x[k] for k in ("name", "resid", "ok") if k in x} for x in closure(q3, set(), BAND) if "resid" in x],
                                      worst_abs_resid=max(abs(x["resid"]) for x in closure(q3, set(), BAND) if "resid" in x))
# strict (won-precision) closure of the recommended scope: every identity except the LOB bridge (Tier-2 legs are whole-백만원 note values) must be exact
strict_after = closure(q3, ALL18, TOL_ID)
lob_resid = [x for x in strict_after if x["name"].startswith("I6")][0]["resid"]
strict_ok = all(x.get("ok", True) for x in strict_after if not x["name"].startswith(("I6", "I7")))
lob_resid_before = [x for x in closure(q3, set(), BAND) if x["name"].startswith("I6")][0]["resid"]


def csm_status(q):
    b = d5[(CODE, q)]["csm"]
    return dict(status=b["status"], master_vector_eok=b["now"], later_vector_eok=b["latest"], pl4_eok=b.get("pl4_eok"), fidelity=b.get("fid"))


gold_in_block = {q: sorted(it for (c, it, qq) in GOLD if qq == q) for q in list(SPEC) + ["2023.4Q"]}
gold_overlap = {q: [it for it in changed.get(q, []) if (CODE, it, q) in GOLD] for q in SPEC}
printed_orig = print_closure(ORIG_VAL[q3], BAND)
printed_later = print_closure(LATER_VAL[q3], TOL_ID)
ok_after_B = scope_closure["B_all_differing_items"]["worst_abs_resid"] <= BAND and strict_ok and not scope_closure["B_all_differing_items"]["gate"]["fail"]
for q in SPEC:
    sp = SPEC[q]
    cen_items = sorted(int(k) for k, vv in d5[(CODE, q)]["its"].items() if vv["master"] is not None and abs(vv["prior"] - vv["master"]) > 1e-3)
    adopt = bool(sp["approved"] and ok_after_B and not gold_overlap[q] and d5[(CODE, q)]["csm"]["status"] == "SAME")
    if not sp["approved"]:
        reason = ("outside the approved list (stays at the old vintage; seam neighbour of 2023.3Q): the master cells are the original-vintage values (16/22/23/24 from the half-year/quarter 경영공시 summary in 억, rounded), "
                  "the FY2024 report prints the restated comparative; owner gold cells in the block: %s" % gold_in_block[q])
    elif adopt:
        reason = ("closes on the merged vector: 20=1+17, |22-24|=|23|, 22=20+21, 31=24+25, 25=sum of OCI parts, 17=18+19 all exact to the won (resid <= 0.002 mn); LOB bridge 1 = 2+13+14+15-16 with the master Tier-2 legs "
                  "residual %+.6f mn (was %+.6f, Tier-2 legs are whole-백만원 note values; gate tolerance max(0.1%%, floor) so unaffected); gate _check_pl_bridge pass=%d fail=%d; no owner gold cell in the block (KR0104 has 0 gold cells); "
                  "CSM latest = master (census SAME, item 4 unchanged so the PL4<->CSM5 pair is untouched); 7 items are a genuine restatement (K-IFRS 1109 classification error correction: 17,18,20,22,23,24,31), "
                  "11 items differ only by the original 백만원 print rounding/footing and are refreshed so that the whole bucket is one 원-precise vector" % (lob_resid, lob_resid_before, scope_closure["B_all_differing_items"]["gate"]["passed"], len(scope_closure["B_all_differing_items"]["gate"]["fail"])))
    else:
        reason = "NOT CLOSED or gold overlap or CSM differs -- see closure lists"
    b = dict(
        quarter=q, adopt=adopt, approved_by_owner=sp["approved"], n_cells=len(changed[q]) if sp["approved"] else 0, items=changed[q] if sp["approved"] else [],
        items_that_differ_from_later_print=changed[q], items_equal_to_later_print=equal_items[q],
        later_filing=dict(fy=sp["later"][0], rcept=RCEPT[sp["later"][0]], file=stmt(sp["later"][0]).rel, statement_title_line=stmt(sp["later"][0]).title,
                          parent_section=stmt(sp["later"][0]).parent, unit=stmt(sp["later"][0]).unit, cumulative_column_position=sp["later"][1] + 1, three_month_column_position=sp["later"][2] + 1),
        census_items=cen_items, gold_cells_in_block=gold_in_block[q], gold_overlap_with_changed_items=gold_overlap[q], user_pl_confirmed_cells_mentions_of_code=CONF_N,
        csm=csm_status(q), reason=reason)
    if sp["approved"]:
        b.update(items_equal_to_census=(cen_items == changed[q]), items_in_census_list=sorted(set(CENSUS_ITEMS)), census_list_subset_of_cells=set(CENSUS_ITEMS) <= set(changed[q]),
                 class_of_items={str(i): klass[i] for i in changed[q]}, scope_decision="B_all_differing_items (recommended); alternatives with closure results in verification.scope_closure",
                 closure_master_before=closure(q, set(), BAND), closure_merged_after_strict=strict_after, closure_printed_later_filing=printed_later, closure_printed_original_filing=printed_orig,
                 gate_master_before=scope_closure["master_before"]["gate"], gate_merged_after=scope_closure["B_all_differing_items"]["gate"],
                 original_filing=dict(fy=sp["orig"][0], rcept=RCEPT[sp["orig"][0]], file=stmt(sp["orig"][0]).rel, statement_title_line=stmt(sp["orig"][0]).title, parent_section=stmt(sp["orig"][0]).parent, unit=stmt(sp["orig"][0]).unit))
    buckets.append(b)

# 2023.4Q annual (information bucket: nothing to adopt)
A_ORIG = read_items(stmt("FY2023_Q4"), 0, 3, helpers=False)
A_LATER = read_items(stmt("FY2024_Q4"), 1, 3, want_ctx="PFY2023dFY", helpers=False)
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
                         master_minus_later=round(m - A_LATER[it]["val"], 6), xml_line_orig=A_ORIG[it]["parts"][0]["line"], xml_line_later=A_LATER[it]["parts"][0]["line"])
q4_max_gap = max(abs(v["master_minus_later"]) for v in q4_status.values())
q4_all_eq_band = q4_max_gap <= 0.001
buckets.append(dict(quarter="2023.4Q", adopt=False, approved_by_owner=False, n_cells=0, items=[], reason=(
    "nothing to adopt: the master 2023.4Q already equals the FY2024 annual report's prior-year column (separate, ctx PFY2023dFY) for all %d items; largest difference %.6f mn (= %.0f won, re-rounding of the restated comparative; "
    "gross lines 투자영업수익/비용 moved +42.2 mn in the comparative but 투자손익 net only 390 won). The 2023.4Q single quarter (annual - 9M) was a MIXED vintage before (annual restated minus 9M original) and becomes consistent after the 2023.3Q adoption: see auto_follow_cells"
    % (len(q4_status), q4_max_gap, q4_max_gap * 1e6)), annual_status=q4_status, gold_cells_in_block=gold_in_block["2023.4Q"]))

# ------------------------------------------------------------------ single quarter analysis (build_pl: 값_당분기 = YTD(q) - YTD(q-1) within the FY; Q1 = YTD; None if an operand is None)
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
for item in range(1, 33):
    for fy in ("2023", "2024"):
        qs = [f"{fy}.{n}Q" for n in (1, 2, 3, 4)]
        ytd = {q: mval(item, q) for q in qs}
        for q in qs:
            dm, dl = derived(ytd, q), mdangi(item, q)
            if (dm is None) != (dl is None) or (dm is not None and abs(dm - dl) > 1e-5):
                model_mismatch.append((item, q, dm, dl))


def src_for_3m(q, item):
    rel = stmt(SPEC[q]["later"][0]).rel
    parts = LATER_3M[q][item]["parts"]
    if len(parts) == 1:
        return f"{rel}:L{parts[0]['line']} [{parts[0]['label']}] {parts[0]['printed']}원"
    return " || ".join(f"{rel}:L{p['line']} [{p['label']}] {p['printed']}원" + ("" if p["contribution_mn"] >= 0 else " (contribution %+.6f)" % p["contribution_mn"]) for p in parts)


for item in POLICY_ITEMS:
    ytd_b = {q: mval(item, q) for q in FYQ}
    ytd_a = {q: adopted_new.get((item, q), mval(item, q)) for q in FYQ}
    for q in FYQ:
        n = int(q[5])
        db_live, da = mdangi(item, q), derived(ytd_a, q)
        db_fresh = derived(ytd_b, q)
        cur_changed = (item, q) in adopted_new
        pq = f"2023.{n-1}Q" if n > 1 else None
        prev_changed = n > 1 and (item, pq) in adopted_new
        rec = dict(quarter=q, item=item, item_name=ITEM_NAME[item], old_live=db_live, old_fresh_build=db_fresh, derived_after_adoption=da,
                   operand_cur=dict(q=q, ytd_before=ytd_b[q], ytd_after=ytd_a[q], adopted=cur_changed),
                   operand_prev=(None if pq is None else dict(q=pq, ytd_before=ytd_b[pq], ytd_after=ytd_a[pq], adopted=prev_changed)))
        if n == 1 or (not cur_changed and not prev_changed):
            rec["class"] = "unchanged_both_old" if n > 1 else "q1_equals_ytd_unchanged"
            rec["why"] = "single quarter = YTD of Q1 (not adopted)" if n == 1 else "both YTD operands stay at the old vintage, nothing changes"
            neighbour_effects.append(rec)
        elif cur_changed and not prev_changed:
            if ytd_b[pq] is None:
                rec["class"] = "blank_before_and_after"
                rec["why"] = "6M (2023.2Q) cumulative is empty in the master, so build_pl derives no single quarter (live is blank as well); nothing is mixed, the cell stays blank"
                neighbour_effects.append(rec)
                continue
            p3 = LATER_3M[q][item]
            new3 = round(p3["val"], 6)
            later_cum = LATER_VAL[q][item]["val"]
            l6 = LATER_VAL[pq][item]["val"]
            rec["class"] = "seam"
            rec["proposed"] = "set_dangi"
            rec["proposed_value"] = new3
            rec["three_month_print"] = dict(value=new3, xml_file=stmt(SPEC[q]["later"][0]).rel, xml_rcept=RCEPT[SPEC[q]["later"][0]],
                                            xml_period_column="prior-year 3-month column (2023.7.1-9.30) of the separate/OFS 4-2 statement, position 3 of 4",
                                            xml_lines=[dict(label=p["label"], line=p["line"], printed=p["printed"], contribution_mn=p["contribution_mn"]) for p in p3["parts"]],
                                            derivation=("direct print" if len(p3["parts"]) == 1 else "sum of printed lines (contributions in xml_lines)"))
            rec["cross_check_9M_minus_6M_both_new_vintage"] = dict(
                later_9M_prior_cum=round(later_cum, 6), fy2024_q2_report_6M_prior_cum=round(l6, 6), difference=round(later_cum - l6, 6), diff_vs_3m_print=round(later_cum - l6 - new3, 6),
                ok=abs(later_cum - l6 - new3) <= TOL_ID, fy2024_q2_line=LATER_VAL[pq][item]["parts"][0]["line"], fy2024_q2_file=stmt(SPEC[pq]["later"][0]).rel)
            rec["old_derived_mixed_vintage"] = round(later_cum - ytd_b[pq], 6)       # new 9M - old 6M (what build_pl would produce without the fix)
            rec["set_dangi_cell"] = [CODE, q, item, new3, src_for_3m(q, item)]
            rec["original_3m_print"] = round(ORIG_3M[q][item]["val"], 6)
            rec["reason"] = ("9M adopted (later vintage), 6M (2023.2Q) stays at the old vintage (경영공시 summary value in 억, outside the approved list) -> build_pl would subtract two vintages "
                             "(it would also resurrect a value that is blank in the live master); the FY2024 Q3 report prints the restated 3-month column -> single quarter = printed 3-month value")
            seam_cells.append(rec)
        elif prev_changed and not cur_changed:
            lat_eq = abs(q4_status[item]["master_minus_later"]) <= 0.001
            rec["class"] = "consistent_after_adoption" if lat_eq else "seam_unresolved"
            rec["why"] = ("annual 2023 (master = FY2023 annual print; equals the FY2024 annual prior print to %.6f mn) is already at the later vintage; 9M adopted now at the later vintage -> annual - 9M has both operands at the same vintage "
                          "(before adoption it mixed the later-vintage annual with the original 9M)" % abs(q4_status[item]["master_minus_later"]) if lat_eq else "annual differs from the later annual print")
            rec["annual_checks"] = dict(master_annual=ytd_b[q], fy2023_annual_print=q4_status[item]["orig_annual_print"], fy2024_annual_prior_print=q4_status[item]["fy2024_annual_prior_print"],
                                        xml_line_orig=q4_status[item]["xml_line_orig"], xml_line_later=q4_status[item]["xml_line_later"])
            auto_follow.append(rec)
        else:
            rec["class"] = "other"
            neighbour_effects.append(rec)

# 3-month print vs live single quarter: are the live 3Q singles all blank for Tier-1 (so what exactly is seam vs blank)?
live_3q_tier1 = {it: mdangi(it, q3) for it in CHECK_ITEMS}
# original 3-month print vs the set_dangi values (3M is the same in both vintages for the unchanged items)
orig3_vs_later3 = []
for item in CHECK_ITEMS:
    o3, l3 = ORIG_3M[q3][item]["val"], LATER_3M[q3][item]["val"]
    orig3_vs_later3.append(dict(item=item, orig_3m=round(o3, 6), later_3m=round(l3, 6), diff=round(l3 - o3, 6), restated=abs(l3 - o3) > BAND))
# single-quarter vector closure after the set_dangi fix (items 16, 22, 23, 24 only exist)
hyb = {item: mdangi(item, q3) for item in range(1, 33)}
for s in seam_cells:
    hyb[s["item"]] = s["proposed_value"]
hyb_close = []
if all(hyb[i] is not None for i in (22, 23, 24)):
    hyb_close.append(dict(name="24 = 22 - 23 (single, 3M prints)", resid=round(hyb[24] - (hyb[22] - hyb[23]), 6), ok=abs(hyb[24] - (hyb[22] - hyb[23])) <= TOL_ID))
L3 = LATER_3M[q3]
for nm, a, b in (("printed 3M: 20 = 1 + 17", L3[20]["val"], L3[1]["val"] + L3[17]["val"]), ("printed 3M: 22 = 20 + 21", L3[22]["val"], L3[20]["val"] + L3[21]["val"]),
                 ("printed 3M: 24 = 22 - 23", L3[24]["val"], L3[22]["val"] - L3[23]["val"]), ("printed 3M: 31 = 24 + 25", L3[31]["val"], L3[24]["val"] + L3[25]["val"])):
    hyb_close.append(dict(name=nm, resid=round(a - b, 6), ok=abs(a - b) <= TOL_ID))

# 4Q single quarter before / after for ALL policy items + closure of the 4Q single vector
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
    for n, a, b in (("20 = 1 + 17", v[20], v[1] + v[17]), ("22 = 20 + 21", v[22], v[20] + v[21]), ("24 = 22 - 23", v[24], v[22] - v[23]), ("31 = 24 + 25", v[31], v[24] + v[25]),
                    ("25 = sum(26..30,32)", v[25], sum(v[i] for i in (26, 27, 28, 29, 30, 32))), ("17 = 18 + 19", v[17], v[18] + v[19]),
                    ("1 = 2+13+14+15-16", v[1], sum((v[i] or 0) for i in (2, 13, 14, 15)) - v[16])):
        cl.append(dict(name=n, resid=round(a - b, 6), ok=abs(a - b) <= TOL_ID))
    q4_close[tag] = cl

# year tie 2023 for the items that carry quarterly singles in the master (16, 22, 23, 24)
tie = {}
for item in POLICY_ITEMS:
    if mval(item, "2023.1Q") is None or mval(item, "2023.2Q") is None:
        continue
    s1 = mval(item, "2023.1Q")
    s2 = mval(item, "2023.2Q") - mval(item, "2023.1Q")
    s3 = [x for x in seam_cells if x["item"] == item][0]["proposed_value"]
    s4 = v4a[item]
    tot = s1 + s2 + s3 + s4
    h1_later = LATER_VAL["2023.2Q"][item]["val"]
    tie[item] = dict(sum_of_four_singles_after=round(tot, 6), master_annual_2023_4Q=mval(item, "2023.4Q"), gap_vs_master_annual=round(tot - mval(item, "2023.4Q"), 6),
                     gap_equals_H1_master_minus_H1_later_print=round(mval(item, "2023.2Q") - h1_later, 6),
                     before_adoption_sum_of_four_live_singles=round(sum((mdangi(item, q) or 0) for q in FYQ), 6),
                     note="the first-half correction was published (FY2024 Q2/Q1 comparatives) but 2023.1Q/2Q are outside the approved list and keep the original-vintage 경영공시 values, so the four singles do not add to the annual by exactly the H1 restatement")

# 2023.1Q / 2023.2Q facts (stay old)
stale_neighbours = {}
for q in ("2023.1Q", "2023.2Q"):
    rows_ = []
    for it in CHECK_ITEMS:
        mv = mval(it, q)
        lp = LATER_VAL[q][it]
        rows_.append(dict(item=it, master=mv, later_print=round(lp["val"], 6), delta=(None if mv is None else round(lp["val"] - mv, 6)), xml_line=lp["parts"][0]["line"]))
    stale_neighbours[q] = dict(items_in_master=[it for it in CHECK_ITEMS if mval(it, q) is not None], items_differing_from_later_print=changed[q], gold_cells_in_block=gold_in_block[q],
                               source_in_master="경영공시 요약 PL (억 단위 반올림) for items 16/22/23/24; other Tier-1 items empty (provenance PL_breakdown_provenance.json DISCLOSURE disclosure_summary_pl)",
                               rows=rows_, later_file=stmt(SPEC[q]["later"][0]).rel, approved=False)

# Tier-2 / helper lines identical in the two vintages (the legs are untouched by the adoption)
leg_lines = {}
for key in ("ins_rev", "reins_rev", "cost_ins", "svc", "reins_cost", "inv_rev", "inv_cost", "nonop_inc", "nonop_exp"):
    o, l = ORIG_VAL[q3]["_h"][key], LATER_VAL[q3]["_h"][key]
    leg_lines[key] = dict(label=o["label"], orig_mn=round(o["val"], 6), later_mn=round(l["val"], 6), delta=round(l["val"] - o["val"], 6), line_orig=o["line"], line_later=l["line"])

csm_cells = {}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    csm_cells[q] = {str(r["항목번호"]): r["값"] for r in csm_rows if r["공시분기"] == q}

verification = dict(
    master_equals_original_print_all=all(abs(mval(it, q3) - ORIG_VAL[q3][it]["val"]) <= 1e-6 for it in CHECK_ITEMS if mval(it, q3) is not None),
    n_master_items_checked_vs_original=len([it for it in CHECK_ITEMS if mval(it, q3) is not None]),
    warnings=warnings, dangi_model_mismatch_vs_live_master=model_mismatch,
    dangi_model_mismatch_note=("pre-existing, not caused by the adoption: the live master has 값_당분기 blank for 2023.3Q items 16/22/23/24 (6M = 억-rounded 경영공시 value) while a fresh build_pl() derives 12114 / -7472 / -1748 / -5724 "
                               "(see KR0104_sim_baseline.txt); the apply step splices build_pl() output, so these four cells MUST be pinned (set_dangi) or they would turn into wrong numbers"),
    census_vs_xml=dict(n_cells=len(cells), max_abs_diff_fsapi_vs_xml=max(abs(c["second_source"]["fsapi"]["diff_vs_xml"]) for c in cells),
                       census_list=CENSUS_ITEMS, census_list_in_plan_cells=sorted(set(CENSUS_ITEMS) & set(changed[q3])), plan_cells_not_in_census_list=sorted(set(changed[q3]) - set(CENSUS_ITEMS)),
                       census_candidate_cells=sorted(i for (qq, i) in cand if qq == q3),
                       candidate_diff_vs_xml={str(c["item"]): c["census_candidate_diff_vs_xml"] for c in cells if c["census_candidate_diff_vs_xml"] is not None and abs(c["census_candidate_diff_vs_xml"]) > 1e-3},
                       candidate_note="cand_pl_cells.json item 18 = 1135383.75571 keeps the rounded item 19 (-1117078) while XML item 19 is -1117077.752608, so 18 differs by 0.2474 mn; the plan takes 18 and 19 from one column"),
    alt_path=dict(n=len([c for c in cells if c["second_source"]["alt_path"]]), n_ok=len([c for c in cells if c["second_source"]["alt_path"] and c["second_source"]["alt_path"]["ok"]]),
                  items_without_alt_path=[c["item"] for c in cells if not c["second_source"]["alt_path"]]),
    restatement_note=dict(n_rows_in_plan=len([c for c in cells if c["second_source"]["restatement_note"]]), within_print_band=len([c for c in cells if c["second_source"]["restatement_note"] and c["second_source"]["restatement_note"]["within_print_band"]]),
                          rows={str(c["item"]): dict(after=c["second_source"]["restatement_note"]["after"]["value"], delta=c["second_source"]["restatement_note"]["delta"]["value"], line_after=c["second_source"]["restatement_note"]["after"]["line"]) for c in cells if c["second_source"]["restatement_note"]},
                          oci_restated_by_note="no: 분기총기타포괄이익 수정 전 482,444 / 수정금액 - / 수정 후 482,444 (FY2024 Q3 L25516-L25518); items 25-30, 32 differ from the later print only by print rounding"),
    gold=dict(KR0104_gold_set_cells=len(GOLD), KR0104_gold_set_keys=sorted([list(k) for k in GOLD]), adopted_cells_hitting_gold=[(c["quarter"], c["item"]) for c in cells if c["gold_cell"]],
              user_pl_confirmed_cells_mentions_of_KR0104=CONF_N, null_dangi_existing=sorted(NULL_D), set_dangi_existing=sorted(SET_D),
              set_dangi_proposed_hitting_existing_null_or_set=[(s["quarter"], s["item"]) for s in seam_cells if (CODE, s["quarter"], s["item"]) in NULL_D or (CODE, s["quarter"], s["item"]) in SET_D]),
    seam_3m_vs_9M_minus_6M=dict(n=len(seam_cells), n_ok=sum(1 for s in seam_cells if s["cross_check_9M_minus_6M_both_new_vintage"]["ok"])),
    original_3m_vs_later_3m=dict(rows=orig3_vs_later3, n_restated=sum(1 for r in orig3_vs_later3 if r["restated"])),
    live_2023_3Q_single_quarter_tier1=live_3q_tier1,
    hybrid_single_2023_3Q_closure=hyb_close,
    tier2_proxy_printed_lines_orig_vs_later_9M=leg_lines,
    scope_closure=scope_closure,
    lob_bridge=dict(master_before_resid_mn=lob_resid_before, merged_after_resid_mn=lob_resid, gate_tolerance="max(0.1% of |item 1|, DEFAULT_FLOOR) in validate_master_tables._check_pl_bridge",
                    note="items 2/3/4..12 (Tier-2 legs) are whole-백만원 values of the original note tables and are not part of the approved Tier-1 refresh; item 15 = 0"),
    q2023_4Q=dict(status=q4_status, max_abs_master_minus_fy2024_annual_prior=q4_max_gap, all_items_equal_within_0_001_mn=q4_all_eq_band, single_quarter=q4_single, single_quarter_closure=q4_close),
    year_tie_2023=tie,
    stale_neighbours=stale_neighbours,
    csm_waterfall_master_cells_unchanged=csm_cells,
    csm=dict(status_2023_3Q=csm_status(q3), note="census: later-filing CSM prior column equals the master (SAME, reader fidelity SAME); CSM_waterfall is not touched; PL item 4 (원수 CSM상각) is not in the plan cells"),
)
plan = dict(code=CODE, company=NAME, generated="2026-10-22", source_tool="data/_derived/remaining_20261022/e19_latest_comparative/KR0104_plan.py", master_unit="백만원",
            statement="separate (OFS) 4-2. 포괄손익계산서 (section 4. 재무제표), prior-year cumulative column of the next-year Q3 report",
            cause="전기오류 정정: K-IFRS 제1109호 최초적용(2023.1.1) 시 일부 금융상품(당기손익-공정가치측정유가증권, 상각후원가측정유가증권)의 SPPI 판단 오류로 인한 분류 오류, FY2024 Q1-Q3 보고서가 비교표시된 2023 분기 손익계산서를 재작성. 순이익 증가(+45,047 백만원, 2023 9M), OCI 불변",
            scope_decision=dict(recommended="B_all_differing_items", n_cells=len(cells), classes={"RESTATED": sorted(i for i in klass if klass[i] == "RESTATED"), "PRINT_ROUNDING": sorted(i for i in klass if klass[i] == "PRINT_ROUNDING")},
                                census_list=CENSUS_ITEMS,
                                why=("The ticket / census list is 17,18,20,22,23,24,28,31. Item 28 moves only by the original print's footing plug (-1.093 mn, the restatement note shows no OCI change), and adopting 28 alone leaves 25 - sum(parts) = %+.3f mn. "
                                     "The rounded original 백만원 prints of the other items differ from the 원-precise later print by < 1.1 mn; refreshing the whole bucket to one column keeps every identity exact to the won (owner rule: rounding differences take the precise side). "
                                     "Alternative A_census_8 (8 cells) and A_restated_only (7 cells) are fully specified in apply_contract.alternatives." % [x for x in scope_closure["A_census_8"]["identities"] if x["name"].startswith("I4")][0]["resid"])),
            buckets=buckets, cells=cells, seam_cells=seam_cells, neighbour_effects=neighbour_effects, auto_follow_cells=auto_follow, verification=verification)


def alt_contract(items):
    cs = [c for c in cells if c["item"] in items]
    return dict(items=sorted(items), n_cells=len(cs), gold_set_cells=[[CODE, c["item"], c["quarter"], c["new"], c["old"]] for c in cs])


plan["apply_contract"] = dict(
    gold_set_cells=[[CODE, c["item"], c["quarter"], c["new"], c["old"]] for c in cells],
    gold_set_notes={f"{c['quarter']}|{c['item']}": c["gold_note"] for c in cells},
    null_dangi_cells=[],
    set_dangi_cells=[s["set_dangi_cell"] for s in seam_cells],
    expected_master_changes=dict(
        value_cells_changed=len(cells),
        dangi_cells_set_by_set_dangi=[[s["quarter"], s["item"], s["old_live"], s["proposed_value"]] for s in seam_cells],
        dangi_cells_auto_follow_2023_4Q=[[a["quarter"], a["item"], a["old_live"], a["derived_after_adoption"]] for a in auto_follow],
        n_dangi_cells_changed_total=len(seam_cells) + len(auto_follow),
        dangi_cells_all_other="unchanged (2023.3Q Tier-1 singles other than 16/22/23/24 stay blank; 2023.1Q/2Q and all FY2024+ unchanged)"),
    provenance_blocks_to_replace=[[CODE, q3, "income_statement"]],
    provenance_note="the 2023.3Q income_statement block is fs_api_tier1 (data/dart/_fs_api_cache/00909349_2023_11014_OFS.json) for items 1,15-17,19-32 and raw_filing_derived for 18; after the gold set the emitter (scripts/emit_pl_provenance.py sandbox copy) decides the block text; contract_notes block unchanged",
    do_not_touch=dict(owner_gold_cells="none exist for KR0104 (user_pl_cells.json has 0 KR0104 entries; user_pl_confirmed_cells.json 0 mentions)", csm_waterfall="unchanged for 2023.3Q (census SAME)",
                      tier2_items="items 2-15 (LOB legs, CSM amortisation, risk adjustment, experience variance) are not in the plan",
                      buckets_not_adopted="2023.1Q and 2023.2Q (outside the approved list; master = 경영공시 summary, 억 rounded), 2023.4Q (master already equals the FY2024 annual prior print), every FY2024/FY2025 bucket (ADDL_OCI_ONLY 2024.4Q/2025.1Q/2025.2Q are a separate decision)"),
    census_note="GOLD_OVERLAY_CENSUS PL tuple: user_pl_cells.json set +%d (KR0104 2023.3Q items %s) and set_dangi.cells +%d (KR0104 2023.3Q items %s); null_dangi +0" % (len(cells), sorted(changed[q3]), len(seam_cells), [s["item"] for s in seam_cells]),
    gate_notes=("adopt 2023.3Q together with the %d set_dangi cells: without them build_pl derives 2023.3Q single = new 9M - old 6M for items 16/22/23/24 (and turns four live blanks into mixed-vintage numbers); "
                "the 2023.4Q single quarters (annual - 9M) move to a consistent vector automatically (%d cells)") % (len(seam_cells), len(auto_follow)),
    alternatives=dict(A_census_8=alt_contract(SCOPES["A_census_8"]), A_restated_only=alt_contract(SCOPES["A_restated_only"]),
                      note="the set_dangi cells are the same in every alternative only if item 16/22/23/24 are adopted; under A_census_8 item 16 stays at 33914 (original print) and its 3Q single is still pinned by set_dangi (3M print is 12,097 in both vintages)"))
(HERE / "plan_KR0104.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

L = []
for b in buckets:
    L.append(f"== {b['quarter']} adopt={b['adopt']} approved={b['approved_by_owner']} cells={b['n_cells']} items={b['items']}")
    if "later_filing" in b:
        L.append(f"   later {b['later_filing']['fy']} rcept {b['later_filing']['rcept']} unit {b['later_filing']['unit']} title L{b['later_filing']['statement_title_line']} parent {b['later_filing']['parent_section']} differ={b['items_that_differ_from_later_print']} equal={b['items_equal_to_later_print']} gold_in_block={b['gold_cells_in_block']}")
    L.append(f"   reason: {b['reason']}")
    for k in ("closure_master_before", "closure_merged_after_strict", "closure_printed_later_filing", "closure_printed_original_filing"):
        if k in b:
            L.append(f"   {k}:")
            for x in b[k]:
                L.append(f"      {x.get('name')}: " + ("SKIP" if ('resid' not in x and 'resids' not in x) else (f"resids={x['resids']} ok={x['ok']}" if 'resids' in x else f"resid={x['resid']} tol={x['tol']} ok={x['ok']}")))
L.append("")
for c in cells:
    ap = c["second_source"]["alt_path"]
    nt = c["second_source"]["restatement_note"]
    L.append(f"CELL {c['quarter']} i{c['item']:>2} {c['item_name']} [{c['cls']}{' census' if c['in_census_list'] else ''}]: old={c['old']} new={c['new']} delta={c['delta']} L{c['xml_line']} fsapi_diff={c['second_source']['fsapi']['diff_vs_xml']} "
             f"cand_diff={c['census_candidate_diff_vs_xml']} alt={'-' if ap is None else (ap['value'], ap['diff_vs_xml'], ap['ok'])} note_after={'-' if nt is None else (nt['after']['value'], nt['delta']['value'], nt['within_print_band'])} "
             f"mastEqOrig={c['master_equals_original_print']} orig_L{c['original_print']['xml_line']} deriv={c['derivation']} lines={[(x['label'], x['line'], x['printed']) for x in c['xml_lines']]}")
L.append("")
L.append(f"SEAM ({len(seam_cells)}):")
for s in seam_cells:
    L.append(f"   {s['quarter']} i{s['item']} old_live={s['old_live']} fresh_build_before={s['old_fresh_build']} mixed_after={s['old_derived_mixed_vintage']} -> {s['proposed']} {s['proposed_value']} 9M-6M check ok={s['cross_check_9M_minus_6M_both_new_vintage']['ok']} (diff {s['cross_check_9M_minus_6M_both_new_vintage']['diff_vs_3m_print']}) orig3M={s['original_3m_print']} line={[(x['label'], x['line'], x['printed']) for x in s['three_month_print']['xml_lines']]}")
L.append(f"AUTO_FOLLOW ({len(auto_follow)}):")
for s in auto_follow:
    L.append(f"   {s['quarter']} i{s['item']} {s['class']} old_live={s['old_live']} after={s['derived_after_adoption']} annual_checks={s['annual_checks']}")
L.append(f"NEIGHBOUR unchanged/blank ({len(neighbour_effects)}):")
for s in neighbour_effects:
    L.append(f"   {s['quarter']} i{s['item']} class={s['class']} old_live={s['old_live']} fresh_before={s['old_fresh_build']} after={s['derived_after_adoption']}")
L.append("SCOPE CLOSURE:")
for k, v in scope_closure.items():
    L.append(f"   {k}: n={v['n']} items={v['items']} gate={v['gate']} worst_abs_resid={v['worst_abs_resid']}")
    for x in v["identities"]:
        L.append(f"        {x['name']}: {x['resid']} ok={x['ok']}")
L.append("VERIFICATION " + json.dumps({k: v for k, v in verification.items() if k not in ('q2023_4Q', 'csm_waterfall_master_cells_unchanged', 'year_tie_2023', 'stale_neighbours', 'scope_closure', 'original_3m_vs_later_3m')}, ensure_ascii=False, default=str))
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
    L.append(f"   {k} " + json.dumps({kk: vv for kk, vv in v.items() if kk != 'rows'}, ensure_ascii=False))
    for r_ in v["rows"]:
        L.append(f"      i{r_['item']} master={r_['master']} later={r_['later_print']} delta={r_['delta']} L{r_['xml_line']}")
L.append("original 3M vs later 3M: " + json.dumps(orig3_vs_later3, ensure_ascii=False))
(HERE / "KR0104_plan_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print("done cells", len(cells), "seam", len(seam_cells), "neighbour", len(neighbour_effects), "auto_follow", len(auto_follow), "warnings", len(warnings), "model_mismatch", len(model_mismatch))
