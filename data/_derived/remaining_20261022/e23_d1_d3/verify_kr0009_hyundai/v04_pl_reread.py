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

lines = []
def P(s=""):
    print(s); lines.append(s)

# --- calibration: current column of FY2024 filings vs master 2024.xQ value
P("=== calibration: FY2024 current cumulative column vs master (WORK) 2024.xQ 값 (백만원)")
cal_bad = 0; cal_n = 0
cur_items = {}
for fy, q in (("FY2024_Q1", "2024.1Q"), ("FY2024_Q2", "2024.2Q"), ("FY2024_Q3", "2024.3Q"), ("FY2024_Q4", "2024.4Q")):
    d, hdr, ti = read_col(fy, "cur")
    it = items_from(d)
    cur_items[q] = it
    for k, v in sorted(it.items()):
        m = W.get((q, k))
        mv = m["값"] if m else None
        cal_n += 1
        if mv is None or abs(mv - v) > 0.0015:
            cal_bad += 1
            P("  calib diff %s item %d reader %.6f master %s" % (q, k, v, mv))
P("calibration cells %d, mismatches %d" % (cal_n, cal_bad))

# --- main: prior column vs WORK/HEAD
res = {}
P("\n=== prior-year cumulative column of FY2024 filings vs master (백만원)")
P("q item name | HEAD | WORK | reader | work-reader | chg(HEAD!=WORK) | stmt line")
n_cell = 0; n_bad = 0; n_chg = 0; n_chg_ok = 0
mism = []
for fy, q in (("FY2024_Q1", "2023.1Q"), ("FY2024_Q2", "2023.2Q"), ("FY2024_Q3", "2023.3Q"), ("FY2024_Q4", "2023.4Q")):
    d, hdr, ti = read_col(fy, "prior")
    P("-- %s prior col header %s ; title line %d" % (fy, hdr, ti))
    it = items_from(d)
    for k in sorted(it):
        hrow = H.get((q, k)); wrow = W.get((q, k))
        hv = hrow["값"] if hrow else "NOROW"; wv = wrow["값"] if wrow else "NOROW"
        v = it[k]
        chg = hv != wv
        diff = (wv - v) if isinstance(wv, (int, float)) else None
        ok = diff is not None and abs(diff) <= 0.0015
        n_cell += 1
        if chg:
            n_chg += 1
            if ok: n_chg_ok += 1
        if not ok:
            n_bad += 1; mism.append((q, k, hv, wv, v))
        P("%s %2d %-28s | %s | %s | %.6f | %s | %s | L%s" % (q, k, (wrow or hrow)["항목명"][:14], hv, wv, v, ("%.6f" % diff) if diff is not None else "NA", "CHG" if chg else "same", line_of(d, k)))
        res[(q, k)] = {"head": hv, "work": wv, "reader": v, "chg": chg, "ok": ok}
P("\nprior-col cells checked %d; mismatches work-vs-reader %d; changed cells %d, of which reader-confirmed %d" % (n_cell, n_bad, n_chg, n_chg_ok))
for m in mism: P("  MISMATCH %s" % (m,))
json.dump({"%s|%d" % k: v for k, v in res.items()}, open(OUT + "v04_pl_reread.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(OUT + "v04_pl_reread.txt", "w", encoding="utf-8").write("\n".join(lines))
