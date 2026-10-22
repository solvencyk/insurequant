"""p_meritz: prototype of the Tier-2 PRIOR-column reader for 메리츠화재 (KR0001; Format-B '보험손익 상세내역' note).
production extract_tier2_sonbo_structured -> _b_note_table(_prefer_ofs(tables)) = FIRST matching table (current period).  prior variant = SECOND matching table (전분기/전반기/전기 twin).
Everything else is the production function body (copied with an `nth` switch).  READ-ONLY.  usage: p_meritz.py <quarters csv>"""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import prod as P  # noqa: E402
import fsapi as F  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T2 = P.T2
_norm, _row_nums = T2._norm, T2._row_nums


def b_note_nth(tables, nth):
    c = 0
    for t in tables:
        if "보험손익" in (t.caption or "") and "상세내역" in (t.caption or ""):
            if any(T2._row_matches(r, T2.B_CSM) for r in t.rows):
                if c == nth:
                    return t
                c += 1
    return None


def structured(tables, nth):
    t = b_note_nth(T2._prefer_ofs(tables), nth)
    if t is None:
        t = b_note_nth(tables, nth)
    if t is None:
        return {}, None
    out = {}
    hb = " ".join(" ".join(h) for h in t.header)
    st = 2 if ("3개월" in hb and "누적" in hb) else 1
    section = None
    sect_keys = {"보험수익": "rev", "보험서비스비용": "cost", "재보험수익": "re_rev", "재보험비용": "re_cost", "총 보험서비스결과": "result"}
    vals = {}

    def col0(r):
        nums = _row_nums(r)
        if not nums:
            return None
        return nums[st - 1] if len(nums) > st - 1 else nums[0]
    totals = {}
    total_labels = {"총 보험수익": "rev", "총 보험서비스비용": "cost", "총 재보험수익": "re_rev", "총 재보험비용": "re_cost"}
    result_row = None
    for r in t.rows:
        lab = _norm(r[0])
        if lab in total_labels:
            totals[total_labels[lab]] = col0(r)
        if lab in sect_keys and (len(_row_nums(r)) == 0 or lab.startswith("총") or lab == "총 보험서비스결과"):
            if lab == "총 보험서비스결과":
                result_row = r
            else:
                section = sect_keys[lab]
            if not _row_nums(r):
                continue
        if section == "rev":
            if T2._row_matches(r, T2.B_CSM):
                vals["csm"] = col0(r)
            elif T2._row_matches(r, T2.B_RA):
                vals["ra"] = col0(r)
            elif T2._row_matches(r, T2.B_REV_EXP):
                vals["rev_exp"] = col0(r)
        elif section == "cost":
            if T2._row_matches(r, T2.B_COST_ACT):
                vals["cost_act"] = col0(r)
        elif section == "re_rev":
            if T2._row_matches(r, T2.B_RE_REV):
                vals["re_rev"] = col0(r)
        elif section == "re_cost":
            if T2._row_matches(r, T2.B_RE_COST):
                vals["re_cost_exp"] = col0(r)
            elif T2._row_matches(r, T2.B_CSM):
                vals["re_csm"] = col0(r)
            elif T2._row_matches(r, T2.B_RA):
                vals["re_ra"] = col0(r)
    if vals.get("csm") is not None:
        out[4] = abs(vals["csm"])
    if vals.get("ra") is not None:
        out[5] = abs(vals["ra"])
    if vals.get("rev_exp") is not None and vals.get("cost_act") is not None:
        out[6] = abs(vals["rev_exp"]) - abs(vals["cost_act"])
    if vals.get("re_csm") is not None:
        out[9] = -abs(vals["re_csm"])
    if vals.get("re_ra") is not None:
        out[10] = -abs(vals["re_ra"])
    if vals.get("re_rev") is not None and vals.get("re_cost_exp") is not None:
        out[11] = abs(vals["re_rev"]) - abs(vals["re_cost_exp"])
    for k, key in (("rev", "_jang_rev"), ("cost", "_jang_cost"), ("re_rev", "_jang_rerev"), ("re_cost", "_jang_recost")):
        if totals.get(k) is not None:
            out[key] = totals[k]
    if result_row is not None:
        nums = _row_nums(result_row)
        if len(nums) >= 3 * st:
            out[13] = nums[3 * st - 1]
            out[14] = nums[-1] - nums[st - 1] - out[13]
    return out, t.line_no


