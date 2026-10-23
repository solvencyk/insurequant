import sys, json, subprocess, time, collections
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
ROOT = vlib.ROOT
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
def jload(p):
    for a in range(3):
        try: return json.load(open(p, encoding="utf-8"))
        except Exception as e:
            time.sleep(30)
    raise
work = {(r["공시분기"], r["항목번호"]): r for r in jload(ROOT + "/PL_breakdown.json") if r["원보험사코드"] == "KR0070"}
hr = subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown.json"], capture_output=True).stdout.decode("utf-8")
head = {(r["공시분기"], r["항목번호"]): r for r in json.loads(hr) if r["원보험사코드"] == "KR0070"}
STMT = {}
def stmt(fy):
    if fy in STMT: return STMT[fy]
    for t in vlib.tables(fy):
        if t["rows"] and any(r["cells"] and r["cells"][0][1].strip() == "보험손익" for r in t["rows"][:3]):
            d = {}
            for r in t["rows"]:
                lab = r["cells"][0][1].strip() if r["cells"] else ""
                if not lab or lab in d: continue
                d[lab] = ([vlib.num(c[1]) for c in r["cells"][1:]], r["line"], [c[0] for c in r["cells"][1:]])
            STMT[fy] = (t, d); return STMT[fy]
    raise SystemExit("no stmt " + fy)
LAB = {1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익(손실)", 21: "영업외손익", 22: "법인세차감전순이익",
       23: "법인세비용(수익)", 24: "당기순이익(손실)", 25: "기타포괄손익", 26: "기타포괄손익-공정가치측정금융자산평가손익",
       27: "보험계약자산(부채)순금융손익", 28: "현금흐름위험회피파생상품평가손익", 30: "재보험계약자산(부채)순금융손익",
       31: "총포괄손익", 32: "기타포괄손익-공정가치측정 신용손실"}
def val(fy, label, col):
    t, d = stmt(fy)
    return d[label][0][col - 1]
def expected(fy, col, item):
    g = lambda l: val(fy, l, col)
    if item in LAB: return g(LAB[item]) / 1e6
    if item == 3: return (g("보험수익") - g("보험비용")) / 1e6
    if item == 8: return (g("재보험수익") - g("재보험비용")) / 1e6
    if item == 2: return expected(fy, col, 3) + expected(fy, col, 8)
    if item == 19: return (g("보험금융수익") + g("재보험금융수익") - g("보험금융비용") - g("재보험금융비용")) / 1e6
    if item == 18: return expected(fy, col, 17) - expected(fy, col, 19)
    return None
ITEMS = [1, 2, 3, 8, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32]
SRC = {"2023.1Q": ("FY2024_Q1", 4, "prior cum"), "2023.2Q": ("FY2024_Q2", 4, "prior cum"), "2023.3Q": ("FY2024_Q3", 4, "prior cum"), "2023.4Q": ("FY2024_Q4", 2, "FY71 col")}
CAL = {"2024.1Q": ("FY2024_Q1", 2), "2024.2Q": ("FY2024_Q2", 2), "2024.3Q": ("FY2024_Q3", 2), "2024.4Q": ("FY2024_Q4", 1)}
out = []
def P(s): out.append(s); 
# header checks
for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"):
    t, d = stmt(fy)
    P("%s table %d-%d header rows: %s" % (fy, t["start"], t["end"], [[c[1] for c in r["cells"]] for r in t["rows"][:2]]))
P("")
P("== calibration: current column of same filings vs master 2024.xQ (unchanged by this load)")
calbad = 0; calok = 0
for q, (fy, col) in CAL.items():
    for it in ITEMS:
        try: e = expected(fy, col, it)
        except KeyError as ex: P("  missing label %s %s" % (fy, ex)); continue
        m = work.get((q, it), {}).get("값")
        if m is None: P("  CAL %s item %d master None expected %.6f" % (q, it, e)); calbad += 1; continue
        ok = abs(m - e) < 2e-6
        if ok: calok += 1
        else: calbad += 1; P("  CAL DIFF %s item %d master %.6f raw %.6f (diff %.6f)" % (q, it, m, e, m - e))
P("calibration ok %d diff %d" % (calok, calbad))
P("")
P("== FY2023 prior columns vs working master (all 20 statement-derivable items x 4 quarters)")
res = []
for q, (fy, col, desc) in SRC.items():
    for it in ITEMS:
        e = expected(fy, col, it)
        w = work.get((q, it), {}).get("값"); h = head.get((q, it), {}).get("값")
        ok = w is not None and abs(w - e) < 2e-6
        moved = (h is None) or (w is None) or abs(h - w) > 1e-9
        stline = stmt(fy)[1].get(LAB.get(it, ""), (None, None, None))[1] if it in LAB else None
        res.append((q, it, e, w, h, ok, moved, stline))
        if not ok: P("  MISMATCH %s item %d raw %.6f master %s head %s" % (q, it, e, w, h))
bad = [r for r in res if not r[5]]
P("checked %d cells; match %d; mismatch %d" % (len(res), len(res) - len(bad), len(bad)))
mv = [r for r in res if r[6]]
P("cells moved vs HEAD (among these 80): %d ; moved & match: %d" % (len(mv), len([r for r in mv if r[5]])))
unmoved_bad = [r for r in res if not r[6] and not r[5]]
P("unmoved but != raw: %d" % len(unmoved_bad))
for r in unmoved_bad: P("   %s item %d raw %.6f master %s" % (r[0], r[1], r[2], r[3]))
P("unmoved and equal raw: %s" % [(r[0], r[1]) for r in res if not r[6] and r[5]])
json.dump([list(r) for r in res], open(OUT + "v07_pl_cells.json", "w", encoding="utf-8"), ensure_ascii=False)
open(OUT + "v07_pl_verify.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
