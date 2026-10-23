import sys, json
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0009_hyundai")
import vlib9, vmaster
from v03_dump_stmt import sep_stmt

OUT = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0009_hyundai/"
H, W = vmaster.load_all("PL_breakdown")

# statement label -> value lookup (first occurrence)
def read_col(fy, which):
    """which: 'cur' | 'prior' ; returns dict label->(value_won_signed, line) and header text"""
    (t, ti), = sep_stmt(fy)
    rows = t["rows"]
    hdr = [c[1] for c in rows[0]["cells"]]
    q4 = fy.endswith("Q4")
    # column index in row cell list (label at 0)
    if q4:
        ci = {"cur": 1, "prior": 2}[which]
        assert "71" in hdr[1] and "70" in hdr[2], hdr
    else:
        ci = {"cur": 2, "prior": 4}[which]
        assert "71" in hdr[1] and "70" in hdr[2], hdr
        sub = [c[1] for c in rows[1]["cells"]]
        assert sub == ["3개월", "누적", "3개월", "누적"], sub
    d = {}
    for r in rows:
        cs = r["cells"]
        if len(cs) <= ci or not cs[0][1]:
            continue
        lab = cs[0][1]
        v = vlib9.num(cs[ci][1])
        if lab not in d:
            d[lab] = (v, r["line"], cs[ci][1])
    return d, hdr, ti

def items_from(d):
    g = lambda lab: d[lab][0]
    out = {}
    out[1] = g("보험손익")
    out[15] = 0.0 if "기타영업수익" not in d else g("기타영업수익")
    out[16] = abs(g("기타사업비용"))
    out[17] = g("투자손익")
    out[19] = g("보험금융수익") + g("재보험금융수익") - abs(g("보험금융비용")) - abs(g("재보험금융비용"))
    out[18] = out[17] - out[19]
    out[20] = g("영업이익(손실)")
    out[21] = g("영업외손익")
    out[22] = g("법인세차감전순이익")
    out[23] = abs(g("법인세비용"))
    out[24] = g("당기순이익(손실)")
    out[25] = g("기타포괄손익")
    out[26] = g("기타포괄손익-공정가치측정채무증권평가손익")
    out[27] = g("보험계약 순금융손익")
    out[28] = g("현금흐름위험회피파생상품평가손익")
    out[29] = g("기타포괄손익-공정가치측정지분증권관련손익")
    out[30] = g("재보험계약 순금융손익")
    out[31] = g("총포괄손익")
    out[32] = out[25] - (out[26] + out[27] + out[28] + out[29] + out[30])
    return {k: v / 1e6 for k, v in out.items()}

def line_of(d, item):
    m = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익(손실)", 21: "영업외손익", 22: "법인세차감전순이익",
         23: "법인세비용", 24: "당기순이익(손실)", 25: "기타포괄손익", 26: "기타포괄손익-공정가치측정채무증권평가손익",
         27: "보험계약 순금융손익", 28: "현금흐름위험회피파생상품평가손익", 29: "기타포괄손익-공정가치측정지분증권관련손익",
         30: "재보험계약 순금융손익", 31: "총포괄손익"}
    if item in m:
        return d[m[item]][1]
    return None

