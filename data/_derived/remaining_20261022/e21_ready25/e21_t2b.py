# -*- coding: utf-8 -*-
"""e21 independent Tier-2 readers, part 2 (롯데 standardized split layout; life income-statement derived items; PL4 notes).  Own code; helpers from e21_t2 / measure-phase mlib only."""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_t2 as T  # noqa: E402
from e21_t2 import M, UNIT_DIV, main_path, nl, part, total  # noqa: E402


def row_label_and_nums(row):
    """leading non-numeric cells = label (joined with '|'), the rest = numeric cells [(val, line, text)]"""
    lab, nums, seen_num = [], [], False
    for c in row["cells"]:
        if not seen_num and c["val"] is None and c["text"].strip() not in ("-", "−", ""):
            lab.append(c["text"])
            continue
        if not seen_num and c["text"].strip() == "":
            continue
        if c["val"] is not None:
            seen_num = True
            nums.append((c["val"], c["line"], c["text"]))
        elif c["text"].strip() in ("-", "−"):
            seen_num = True
            nums.append((0.0, c["line"], c["text"]))
    return nl("|".join(lab)), nums


def lotte_split_read(code, q):
    """FY2025 Q2/Q3 standardized note tables: heading table ('... 분석 공시, ...') -> current data table -> marker table ('전반기 (단위 : 백만원)') -> PRIOR data table.
    Columns per table: [장기, 일반, 자동차, 합계] x [3개월, 누적] = 8 numeric cells; 누적 = index 2k+1."""
    fy = M.later_fy(q)
    path = main_path(code, fy)
    lines = M.read_lines(path)
    tabs = list(M.iter_tables(lines))
    prior, pend, state, unit = {}, None, None, None
    for t in tabs:
        if not t["rows"]:
            continue
        r0 = nl(" ".join(c["text"] for c in t["rows"][0]["cells"]))
        if len(t["rows"]) <= 2 and "분석공시" in r0:
            if "재보험비용의보험서비스비용분석공시" in r0:
                leg = "re_rev"
            elif "재보험비용분석공시" in r0:
                leg = "re_cost"
            elif "재보험수익분석공시" in r0:
                leg = "re_rev"
            elif "보험서비스비용분석공시" in r0 and "재보험" not in r0:
                leg = "cost"
            elif "보험수익분석공시" in r0:
                leg = "rev"
            else:
                leg = None
            kind = "tot" if r0.endswith("합계") else ("paa" if r0.endswith("보험료배분접근법을적용한보험계약") else ("nonpaa" if "외의보험계약" in r0 else "single"))
            pend = (leg, kind) if leg else None
            state = "after_heading" if leg else None
            continue
        is_data = len(t["rows"]) >= 6
        if state == "after_heading" and is_data:
            state = "after_cur"
            continue
        if state == "after_cur" and len(t["rows"]) == 1 and r0.startswith(("전반기", "전분기")):
            m = re.search(r"단위\s*[:：]?\s*(백만원|천원|원)", " ".join(c["text"] for c in t["rows"][0]["cells"]))
            unit = m.group(1) if m else None
            state = "after_marker"
            continue
        if state == "after_marker" and is_data:
            leg, kind = pend
            prior.setdefault(leg, []).append(dict(kind=kind, table=t, unit=unit))
            state = None
    if not all(k in prior for k in ("rev", "cost", "re_rev", "re_cost")):
        raise RuntimeError(f"{path.name}: prior legs found {list(prior)} (need rev/cost/re_rev/re_cost)")
    units = {e["unit"] for v in prior.values() for e in v}
    if len(units) != 1 or None in units:
        raise RuntimeError(f"{path.name}: units of the prior tables {units}")
    unit = units.pop()
    div = UNIT_DIV[unit]

    def comp(leg, needles, lob_idx=1):
        for e in prior[leg]:
            for r in e["table"]["rows"]:
                lab, nums = row_label_and_nums(r)
                if nums and any(nl(n) in lab for n in needles):
                    if len(nums) != 8:
                        raise RuntimeError(f"row {lab[:50]} has {len(nums)} numeric cells (need 8 = 4 columns x [3개월, 누적])")
                    return nums[lob_idx], lab, e["table"]["start"], lob_idx
        return None

    def grand(leg):
        e = prior[leg][-1]
        for r in reversed(e["table"]["rows"]):
            lab, nums = row_label_and_nums(r)
            if nums:
                if len(nums) != 8:
                    raise RuntimeError(f"grand row {lab[:50]} has {len(nums)} numeric cells")
                return r, lab, nums, e["table"]["start"]
        return None

    def P(found, label, sign=1, absv=False):
        c, lab, tstart, col = found
        return part(f"{label} [{lab[:60]}@table L{tstart}]", c, sign, absv, col, div)

    out = {}

    def item(i, parts, formula):
        out[i] = dict(val=total(parts), parts=parts, formula=formula)

    csm = comp("rev", ["보험계약마진상각", "서비스의이전으로당기손익에인식한보험계약마진"])
    ra = comp("rev", ["위험조정변동", "비금융위험에대한위험조정의변동분"])
    rev_exp = comp("rev", ["예상보험금및예상기타보험서비스비용", "보고기간에발생한보험서비스비용"])
    cost_act = comp("cost", ["발생보험금및기타서비스비용", "발생한보험금및그밖의발생한보험서비스비용"])
    re_csm = comp("re_cost", ["보험계약마진상각", "서비스의이전으로당기손익에인식한보험계약마진"])
    re_ra = comp("re_cost", ["위험조정변동", "비금융위험에대한위험조정의변동분"])
    re_rev_act = comp("re_rev", ["발생보험금및기타재보험수익"])
    re_cost_exp = comp("re_cost", ["회수예상보험금및기타보험서비스비용", "보고기간에발생한보험서비스비용"])
    item(4, [P(csm, "원수 CSM상각", 1, True)], "|보험계약마진 상각(보험수익 구간, 장기 누적)|")
    item(5, [P(ra, "원수 RA", 1, True)], "|위험조정 변동(보험수익 구간, 장기 누적)|")
    item(6, [P(rev_exp, "예상보험금", 1, False), P(cost_act, "발생보험금", -1, False)], "예상보험금 - 발생보험금")
    item(9, [P(re_csm, "재보험 CSM", -1, True)], "-|보험계약마진 상각(재보험비용 구간)|")
    item(10, [P(re_ra, "재보험 RA", -1, True)], "-|위험조정 변동(재보험비용 구간)|")
    item(11, [P(re_rev_act, "회수가능", 1, True), P(re_cost_exp, "회수예상", -1, True)], "|발생보험금 및 기타재보험수익| - |회수예상 보험금|")
    G = {leg: grand(leg) for leg in ("rev", "cost", "re_rev", "re_cost")}

    def GP(leg, lob_pos, label, sign):
        r, lab, nums, tstart = G[leg]
        idx = 2 * lob_pos + 1
        return part(f"{label} [{lab[:60]}@table L{tstart}]", nums[idx], sign, False, idx, div)

    item(3, [GP("rev", 0, "발행 보험수익 합(장기)", 1), GP("cost", 0, "발행 보험서비스비용 합(장기)", -1)], "보험수익 grand(장기 누적) - 보험서비스비용 grand(장기 누적)")
    item(8, [GP("re_rev", 0, "재보험수익 합(장기)", 1), GP("re_cost", 0, "재보험비용 합(장기)", -1)], "재보험수익 grand(장기 누적) - 재보험비용 grand(장기 누적)")
    item(14, [GP("rev", 1, "보험수익(일반)", 1), GP("cost", 1, "보험서비스비용(일반)", -1), GP("re_rev", 1, "재보험수익(일반)", 1), GP("re_cost", 1, "재보험비용(일반)", -1)], "일반 열: 보험수익 - 보험비용 + 재보험수익 - 재보험비용")
    item(13, [GP("rev", 2, "보험수익(자동차)", 1), GP("cost", 2, "보험서비스비용(자동차)", -1), GP("re_rev", 2, "재보험수익(자동차)", 1), GP("re_cost", 2, "재보험비용(자동차)", -1)], "자동차 열: 보험수익 - 보험비용 + 재보험수익 - 재보험비용")
    starts = [e["table"]["start"] for leg in prior.values() for e in leg]
    return {i: dict(v, src=f"{M.rel(path)} prior tables {starts} unit {unit}") for i, v in out.items()}
