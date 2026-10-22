# -*- coding: utf-8 -*-
"""e21 independent Tier-2 / derived-item readers (own code; imports only the measure-phase line reader mlib + e21_read, NOT scripts/ or src/ handlers).
Each reader returns {item: dict(val (백만원), parts=[dict(label, line, printed, sign, abs, col)], formula)} for the LATER filing's prior-period column,
with physical xml line numbers for every printed cell it used.  Item definitions follow scripts/build_pl_breakdown.py::assemble (read, not imported):
  3 = 장기 보험수익합 - 보험서비스비용합 ; 8 = 장기 재보험수익합 - 재보험비용합 ; 2 = 3 + 8 ; 7 = 3 - (4+5+6) ; 12 = 8 - (9+10+11)
  4 = |CSM상각| ; 5 = |위험조정변동| ; 6 = |예상보험금| - |발생보험금| ; 9 = -|재보험 CSM| ; 10 = -|재보험 RA| ; 11 = |회수가능| - |회수예상| ; 13 = 자동차 ; 14 = 일반(+해외)
"""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402  (own line-oriented table reader, measure phase)
import stmtlib as S  # noqa: E402

UNIT_DIV = {"원": 1e6, "천원": 1e3, "백만원": 1.0}


def nl(s):
    return re.sub(r"\s+", "", (s or "").replace("\u3000", ""))


def sep_notes_from(lines):
    v = 0
    for ln, tt in S.titles(lines):
        if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", tt)):
            v = ln
    return v


def unit_above(lines, start, span=60):
    """unit of a note table: nearest '(단위 : X)' within `span` lines above the table or inside its caption paragraph"""
    for k in range(start - 1, max(start - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", re.sub(r"<[^>]+>", "", lines[k]))
        if m:
            return m.group(1), k + 1
    return None, None


def nums_of(row, skip=1):
    """numeric cells of a table row after the label cell(s): [(val, line, text)]"""
    out = []
    for c in row["cells"][skip:]:
        if c["val"] is not None:
            out.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "−"):
            out.append((0.0, c["line"], c["text"]))
    return out


class Part(dict):
    pass


def part(label, cell, sign=1, absv=False, col=None, unit_div=1.0):
    v, ln, tx = cell
    unit = {1e6: "원", 1e3: "천원", 1.0: "백만원"}[unit_div]
    return dict(label=label, line=ln, printed=tx, sign=sign, abs=absv, col=col, unit=unit, contribution_mn=round(sign * (abs(v) if absv else v) / unit_div, 6))


def total(parts):
    return sum(p["contribution_mn"] for p in parts)


# ================================================================================================ KB손해보험 (KR0010)
def kb_read(code, q):
    """KB손보 '(N) 당기와 전기 중 보험손익의 상세내역' (separate basis): columns [장기, 일반, 자동차, 해외, 합계] (분기/반기: 3개월 half + 누적 half). The SECOND table of the twin pair is the prior period."""
    fy = M.later_fy(q)
    path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
    lines = M.read_lines(path)
    s0 = sep_notes_from(lines)
    cands = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        cap = t["caption"] or ""
        if "보험손익" not in cap or "상세" not in cap:
            continue
        labs = [nl(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
        if "총보험서비스결과" not in labs or "총보험수익" not in labs:
            continue
        cands.append(t)
    if len(cands) < 2:
        raise RuntimeError(f"{path.name}: expected a twin pair of KB 보험손익 상세내역 tables in the separate notes, found {len(cands)}")
    t = cands[1]   # prior period
    hdr = nl(" ".join(c["text"] for r in t["rows"][:4] for c in r["cells"]))
    cum = "3개월" in hdr and "누적" in hdr
    unit = find_unit(lines, t)
    div = UNIT_DIV[unit]

    def pick(row):
        n = nums_of(row)
        if not n:
            return None
        return n[len(n) // 2] if cum else n[0], (len(n) // 2 if cum else 0)

    def rows_by(*labs, nth=1, exact=False):
        hit = [r for r in t["rows"] if r["cells"] and ((nl(r["cells"][0]["text"]) in [nl(x) for x in labs]) if exact else any(nl(x) in nl(r["cells"][0]["text"]) for x in labs))]
        return hit[nth - 1] if len(hit) >= nth else None

    def cell(row, which="jang"):
        n = nums_of(row)
        half = n[len(n) // 2:] if cum else n
        if which == "jang":
            return half[0], (len(n) // 2 if cum else 0)
        return half[which], ((len(n) // 2 + which) if cum else which)

    L = {}
    L["csm"] = rows_by("제공된 서비스의 보험계약마진", "보험계약마진 상각")
    L["ra"] = rows_by("위험해제로 인한 위험조정의 변동", nth=1)
    L["rev_exp"] = rows_by("예상 보험금 및 보험서비스비용")
    L["cost_act"] = rows_by("보험금 및 보험서비스비용", exact=True)
    L["re_csm"] = rows_by("제공받은 서비스의 재보험계약마진")
    L["re_cost_exp"] = rows_by("회수예상 보험금 및 보험서비스비용")
    L["re_ra"] = rows_by("위험해제로 인한 위험조정의 변동", nth=2)
    L["re_rev"] = rows_by("회수가능 보험금 및 보험서비스비용")
    L["tr"] = rows_by("총 보험수익", exact=True)
    L["tc"] = rows_by("총 보험서비스비용", exact=True)
    L["trr"] = rows_by("총 재보험수익", exact=True)
    L["trc"] = rows_by("총 재보험비용", exact=True)
    L["res"] = rows_by("총 보험서비스결과", exact=True)
    out = {}

    def P(key, label, sign=1, absv=False, which="jang"):
        c, col = cell(L[key], which)
        return part(f"{label} [{M.norm_label(L[key]['cells'][0]['text'])}]", c, sign, absv, col, div)

    def item(i, parts, formula):
        out[i] = dict(val=total(parts), parts=parts, formula=formula, src=f"{M.rel(path)} table@L{t['start']} unit {unit}")

    item(4, [P("csm", "원수 CSM상각", 1, True)], "|제공된 서비스의 보험계약마진(장기)|")
    item(5, [P("ra", "원수 위험조정", 1, True)], "|위험해제로 인한 위험조정의 변동(장기, 보험수익)|")
    item(6, [P("rev_exp", "예상 보험금", 1, True), P("cost_act", "발생 보험금", -1, True)], "|예상 보험금| - |보험금 및 보험서비스비용|")
    item(9, [P("re_csm", "재보험 CSM", -1, True)], "-|제공받은 서비스의 재보험계약마진|")
    item(10, [P("re_ra", "재보험 RA", -1, True)], "-|위험해제로 인한 위험조정의 변동(재보험비용)|")
    item(11, [P("re_rev", "회수가능", 1, True), P("re_cost_exp", "회수예상", -1, True)], "|회수가능 보험금| - |회수예상 보험금|")
    item(3, [P("tr", "총 보험수익(장기)", 1, False), P("tc", "총 보험서비스비용(장기)", -1, True)], "총 보험수익(장기) - |총 보험서비스비용(장기)|")
    item(8, [P("trr", "총 재보험수익(장기)", 1, False), P("trc", "총 재보험비용(장기)", -1, True)], "총 재보험수익(장기) - |총 재보험비용(장기)|")
    item(13, [P("res", "총 보험서비스결과(자동차)", 1, False, which=2)], "총 보험서비스결과 자동차 열")
    item(14, [P("res", "총 보험서비스결과(일반)", 1, False, which=1), P("res", "총 보험서비스결과(해외)", 1, False, which=3)], "총 보험서비스결과 일반 + 해외 열")
    out["_jang_net"] = dict(val=total([P("res", "총 보험서비스결과(장기)", 1, False, which="jang")]), parts=[P("res", "총 보험서비스결과(장기)", 1, False, which="jang")], formula="총 보험서비스결과 장기 열 (item 2 fallback)")
    return out


def derive_2_3_7_8_12(r, master4, master5, master6, master9, master10, master11):
    """items 2/7/12 from the read items + the master note values the quarter keeps (4,5,6,9,10,11 not restated)"""
    v = {i: r[i]["val"] for i in r if isinstance(i, int)}
    g = lambda i, m: v[i] if i in v else m  # noqa: E731
    out = {}
    if 3 in v and 8 in v:
        out[2] = v[3] + v[8]
    if 3 in v and None not in (g(4, master4), g(5, master5), g(6, master6)):
        out[7] = v[3] - (g(4, master4) + g(5, master5) + g(6, master6))
    if 8 in v and None not in (g(9, master9), g(10, master10), g(11, master11)):
        out[12] = v[8] - (g(9, master9) + g(10, master10) + g(11, master11))
    return out


# ------------------------------------------------------------------------------------------------ shared helpers (unit / twin tables / section walkers)
def find_unit(lines, t, span=40):
    """unit printed with a note table: inside the table, in its caption, or within `span` lines above (explicit; no default)"""
    blob = " ".join(c["text"] for r in t["rows"][:3] for c in r["cells"]) + " " + (t.get("caption") or "")
    m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", blob)
    if m:
        return m.group(1)
    for k in range(t["start"] - 1, max(t["start"] - span, 0), -1):
        m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", re.sub(r"<[^>]+>", "", lines[k]))
        if m:
            return m.group(1)
    raise RuntimeError(f"unit of table@L{t['start']} not found")


def main_path(code, fy):
    return [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]


def lobcols(t):
    """column layout of a [장기, 일반, 자동차, (해외/합계)] note table -> dict(cum: bool, step: 1|2)"""
    hdr = nl(" ".join(c["text"] for r in t["rows"][:6] for c in r["cells"]))
    cum = "3개월" in hdr and "누적" in hdr
    return dict(cum=cum, step=2 if cum else 1)


def at(row, idx):
    n = nums_of(row)
    return n[idx] if len(n) > idx else None


def sect_rows(t, heads):
    """walk the rows of a combined note table; `heads` maps a section-header label (no numbers) to a key; returns {key: [row, ...]} in order"""
    out, cur = {}, None
    for r in t["rows"]:
        if not r["cells"]:
            continue
        lab = nl(r["cells"][0]["text"])
        if lab in heads and not nums_of(r):
            cur = heads[lab]
            out.setdefault(cur, [])
            continue
        if cur is not None:
            out[cur].append(r)
    return out


def row_find(rows, needles, exclude=(), startswith=False):
    for r in rows:
        lab = nl(r["cells"][0]["text"]) + (nl(r["cells"][1]["text"]) if len(r["cells"]) > 1 and not nums_of(r)[:0] and r["cells"][1]["val"] is None else "")
        if startswith:
            ok = any(lab.startswith(nl(x)) for x in needles)
        else:
            ok = any(nl(x) in lab for x in needles)
        if ok and not any(nl(e) in lab for e in exclude):
            return r
    return None


def mk(items, path, t, unit, extra=""):
    return {i: dict(v, src=f"{M.rel(path)} table@L{t['start']} unit {unit}{extra}") for i, v in items.items()}


# ================================================================================================ 롯데손해보험 (KR0003): combined single table ('bycontent') of the later filing
def lotte_combined_read(code, q):
    """FY2024 Q1/Q2, FY2025 Q1: ONE table '보험손익 및 재보험손익' with section header rows 보험수익 / 보험비용 / 재보험수익 / 재보험비용 and columns [장기, 일반, 자동차, 합계]
    (반기: each column split into [3개월, 누적]); the SECOND such table of the twin pair is the prior period."""
    fy = M.later_fy(q)
    path = main_path(code, fy)
    lines = M.read_lines(path)
    cands = []
    for t in M.iter_tables(lines):
        labs0 = {nl(r["cells"][0]["text"]) for r in t["rows"] if r["cells"] and not nums_of(r)}
        if {"보험수익", "보험비용", "재보험수익", "재보험비용"} <= labs0 and any(nl(c["text"]).startswith("장기") for r in t["rows"][:4] for c in r["cells"]):
            cands.append(t)
    if len(cands) < 2:
        raise RuntimeError(f"{path.name}: {len(cands)} combined 롯데 tables (need the twin pair)")
    t = cands[1]
    unit = find_unit(lines, t)
    div = UNIT_DIV[unit]
    cl = lobcols(t)
    sec = sect_rows(t, {"보험수익": "rev", "보험비용": "cost", "재보험수익": "re_rev", "재보험비용": "re_cost"})
    off = cl["step"] - 1       # 누적 = 2nd of each (3개월, 누적) pair

    def P(rows, needles, label, sign=1, absv=False, lob=0, exclude=(), startswith=False):
        r = row_find(rows, needles, exclude, startswith)
        if r is None:
            raise KeyError(f"row {needles} not found in section ({label})")
        c = at(r, lob * cl["step"] + off)
        return part(f"{label} [{nl(r['cells'][0]['text'])}]", c, sign, absv, lob * cl["step"] + off, div)

    out = {}

    def item(i, parts, formula):
        out[i] = dict(val=total(parts), parts=parts, formula=formula)

    item(4, [P(sec["rev"], ["보험계약마진상각"], "원수 CSM상각", 1, True)], "|보험계약마진 상각(보험수익 구간, 장기)|")
    item(5, [P(sec["rev"], ["위험조정변동"], "원수 RA", 1, True)], "|위험조정 변동(보험수익 구간, 장기)|")
    item(6, [P(sec["rev"], ["예상보험금및예상기타보험서비스비용"], "예상보험금", 1, False), P(sec["cost"], ["발생보험금및기타서비스비용"], "발생보험금", -1, False)], "예상보험금 - 발생보험금 (부호 인쇄값 그대로)")
    item(9, [P(sec["re_cost"], ["보험계약마진상각"], "재보험 CSM", -1, True)], "-|보험계약마진 상각(재보험비용 구간)|")
    item(10, [P(sec["re_cost"], ["위험조정변동"], "재보험 RA", -1, True)], "-|위험조정 변동(재보험비용 구간)|")
    item(11, [P(sec["re_rev"], ["발생보험금및기타재보험수익"], "회수가능", 1, True), P(sec["re_cost"], ["회수예상보험금및기타보험서비스비용"], "회수예상", -1, True)], "|발생보험금 및 기타재보험수익| - |회수예상 보험금|")
    rev_t = lambda lob, sg, ab: P(sec["rev"], ["총보험수익"], "총 보험수익", sg, ab, lob, startswith=True)  # noqa: E731
    cost_t = lambda lob, sg, ab: P(sec["cost"], ["총보험비용"], "총 보험비용", sg, ab, lob, startswith=True)  # noqa: E731
    rr_t = lambda lob, sg, ab: P(sec["re_rev"], ["총재보험수익"], "총 재보험수익", sg, ab, lob, startswith=True)  # noqa: E731
    rc_t = lambda lob, sg, ab: P(sec["re_cost"], ["총재보험비용"], "총 재보험비용", sg, ab, lob, startswith=True)  # noqa: E731
    item(3, [rev_t(0, 1, False), cost_t(0, -1, False)], "총 보험수익(장기) - 총 보험비용(장기)")
    item(8, [rr_t(0, 1, False), rc_t(0, -1, False)], "총 재보험수익(장기) - 총 재보험비용(장기)")
    item(14, [rev_t(1, 1, False), cost_t(1, -1, False), rr_t(1, 1, False), rc_t(1, -1, False)], "일반 열: 보험수익 - 보험비용 + 재보험수익 - 재보험비용")
    item(13, [rev_t(2, 1, False), cost_t(2, -1, False), rr_t(2, 1, False), rc_t(2, -1, False)], "자동차 열: 보험수익 - 보험비용 + 재보험수익 - 재보험비용")
    return mk(out, path, t, unit)


# ================================================================================================ 메리츠화재 (KR0001): Format-B '(4) 보험손익 상세내역' (separate basis), twin pair
def meritz_read(code, q):
    fy = M.later_fy(q)
    path = main_path(code, fy)
    lines = M.read_lines(path)
    s0 = sep_notes_from(lines)
    cands = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        cap = t["caption"] or ""
        if "보험손익" not in cap or "상세내역" not in cap:
            continue
        labs = [nl(r["cells"][0]["text"]) for r in t["rows"] if r["cells"]]
        if "당기손익으로인식한보험계약마진금액" not in labs or "총보험서비스결과" not in labs:
            continue
        cands.append(t)
    if len(cands) < 2:
        raise RuntimeError(f"{path.name}: {len(cands)} 메리츠 보험손익 상세내역 tables in the separate notes (need the twin pair)")
    t = cands[1]
    unit = find_unit(lines, t)
    div = UNIT_DIV[unit]
    cl = lobcols(t)
    st, off = cl["step"], cl["step"] - 1
    heads = {"보험수익": "rev", "보험서비스비용": "cost", "재보험수익": "re_rev", "재보험비용": "re_cost"}
    sec = sect_rows(t, heads)

    def P(rows, label_eq, desc, sign=1, absv=False, lob=0):
        hit = [r for r in rows if nl(r["cells"][0]["text"]) == nl(label_eq)]
        if len(hit) != 1:
            raise KeyError(f"{desc}: {len(hit)} rows labelled {label_eq!r}")
        c = at(hit[0], lob * st + off)
        return part(f"{desc} [{nl(label_eq)}]", c, sign, absv, lob * st + off, div)

    out = {}

    def item(i, parts, formula):
        out[i] = dict(val=total(parts), parts=parts, formula=formula)

    item(4, [P(sec["rev"], "당기손익으로 인식한 보험계약마진 금액", "원수 CSM상각", 1, True)], "|당기손익으로 인식한 보험계약마진 금액(보험수익 구간, 장기)|")
    item(5, [P(sec["rev"], "위험해제에 따른 위험조정 변동", "원수 RA", 1, True)], "|위험해제에 따른 위험조정 변동(보험수익 구간, 장기)|")
    item(6, [P(sec["rev"], "예상보험금 및 보험서비스비용", "예상보험금", 1, True), P(sec["cost"], "보험금 및 보험서비스비용", "발생보험금", -1, True)], "|예상보험금| - |보험금 및 보험서비스비용(보험서비스비용 구간)|")
    item(9, [P(sec["re_cost"], "당기손익으로 인식한 보험계약마진 금액", "재보험 CSM", -1, True)], "-|당기손익으로 인식한 보험계약마진 금액(재보험비용 구간)|")
    item(10, [P(sec["re_cost"], "위험해제에 따른 위험조정 변동", "재보험 RA", -1, True)], "-|위험해제에 따른 위험조정 변동(재보험비용 구간)|")
    item(11, [P(sec["re_rev"], "회수가능 보험금 및 보험서비스비용", "회수가능", 1, True), P(sec["re_cost"], "회수예상 보험금 및 보험서비스비용", "회수예상", -1, True)], "|회수가능| - |회수예상|")
    allrows = t["rows"]
    item(3, [P(allrows, "총 보험수익", "총 보험수익(장기)", 1, False), P(allrows, "총 보험서비스비용", "총 보험서비스비용(장기)", -1, False)], "총 보험수익(장기) - 총 보험서비스비용(장기)")
    item(8, [P(allrows, "총 재보험수익", "총 재보험수익(장기)", 1, False), P(allrows, "총 재보험비용", "총 재보험비용(장기)", -1, False)], "총 재보험수익(장기) - 총 재보험비용(장기)")
    res = [r for r in allrows if nl(r["cells"][0]["text"]) == "총보험서비스결과"]
    n = nums_of(res[0])
    if len(n) < 3 * st:
        raise RuntimeError("총 보험서비스결과 row too short")
    c13 = n[3 * st - 1]
    item(13, [part("총 보험서비스결과(자동차) [총보험서비스결과]", c13, 1, False, 3 * st - 1, div)], "총 보험서비스결과 자동차 열(누적)")
    item(14, [part("총 보험서비스결과(합계) [총보험서비스결과]", n[-1], 1, False, len(n) - 1, div),
              part("총 보험서비스결과(장기) [총보험서비스결과]", n[st - 1], -1, False, st - 1, div),
              part("총 보험서비스결과(자동차) [총보험서비스결과]", c13, -1, False, 3 * st - 1, div)], "일반 = 합계 - 장기 - 자동차")
    return mk(out, path, t, unit)
