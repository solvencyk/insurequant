import sys, json, subprocess, collections
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib
ROOT = vlib.ROOT
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
rows = [r for r in json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"]
hr = subprocess.run(["git", "-C", ROOT, "show", "HEAD:PL_breakdown.json"], capture_output=True).stdout.decode("utf-8")
hrows = [r for r in json.loads(hr) if r["원보험사코드"] == "KR0070"]
W = {(r["공시분기"], r["항목번호"]): r for r in rows}; H = {(r["공시분기"], r["항목번호"]): r for r in hrows}
gold = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
nulls = set(); sets = set()
for c in gold["null_dangi"]["cells"]:
    if c[0] == "KR0070": nulls.add((c[1], c[2]))
for c in gold["set_dangi"]["cells"]:
    if c[0] == "KR0070": sets.add((c[1], c[2]))
L = []
L.append("KR0070 null_dangi %s ; set_dangi %s" % (sorted(nulls), sorted(sets)))
def prevq(q):
    y, k = q.split("."); n = int(k[0]); return None if n == 1 else "%s.%dQ" % (y, n - 1)
bad = 0; checked = 0; pinned_skipped = 0
changed_dangi = []
for (q, it), r in sorted(W.items()):
    v = r.get("값"); d = r.get("값_당분기")
    p = prevq(q)
    if p is None: exp = v
    else:
        pv = W.get((p, it), {}).get("값")
        exp = None if (v is None or pv is None) else v - pv
    if (q, it) in nulls or (q, it) in sets:
        pinned_skipped += 1; continue
    checked += 1
    ok = (exp is None and d is None) or (exp is not None and d is not None and abs(exp - d) < 1e-6)
    if not ok:
        bad += 1; L.append("  DANGI MISMATCH %s item %d 값=%s 값_당분기=%s expected=%s" % (q, it, v, d, exp))
L.append("checked %d (all KR0070 PL cells, all quarters), mismatches %d, pinned-skipped %d" % (checked, bad, pinned_skipped))
# changed dangi cells vs HEAD
chg = [(k, H[k].get("값_당분기"), W[k].get("값_당분기")) for k in W if k in H and H[k].get("값_당분기") != W[k].get("값_당분기")]
L.append("값_당분기 changed vs HEAD: %d ; by quarter %s" % (len(chg), dict(collections.Counter(k[0] for k, a, b in chg))))
chgv = {k for k in W if k in H and H[k].get("값") != W[k].get("값")}
follow = [k for k, a, b in chg if k not in chgv]
L.append("of which 값 itself unchanged (follow-on): %d -> %s" % (len(follow), sorted(follow)))
# every changed dangi equals recompute? (covered by checked above); report any changed dangi in the null/set list
L.append("changed dangi in pinned set: %s" % [k for k, a, b in chg if k in nulls or k in sets])
# any dangi changes in quarters outside 2023
L.append("changed dangi outside 2023: %s" % [k for k, a, b in chg if not k[0].startswith("2023")])
# 2024.1Q dangi check vs hr
# seam 3-month check (statement items) via filings
import importlib.util
spec = importlib.util.spec_from_file_location("v07", OUT + "v07_pl_verify.py")
# reuse functions by exec of a trimmed copy: re-implement minimal
def stmt(fy):
    for t in vlib.tables(fy):
        if t["rows"] and any(r["cells"] and r["cells"][0][1].strip() == "보험손익" for r in t["rows"][:3]):
            d = {}
            for r in t["rows"]:
                lab = r["cells"][0][1].strip() if r["cells"] else ""
                if not lab or lab in d: continue
                d[lab] = [vlib.num(c[1]) for c in r["cells"][1:]]
            return d
S = {fy: stmt(fy) for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4")}
labs = ["보험손익", "보험수익", "보험비용", "재보험수익", "재보험비용", "기타사업비용", "투자손익", "보험금융수익", "재보험금융수익", "보험금융비용", "재보험금융비용",
        "영업이익(손실)", "영업외손익", "법인세차감전순이익", "법인세비용(수익)", "당기순이익(손실)", "기타포괄손익", "기타포괄손익-공정가치측정금융자산평가손익",
        "보험계약자산(부채)순금융손익", "현금흐름위험회피파생상품평가손익", "재보험계약자산(부채)순금융손익", "총포괄손익", "기타포괄손익-공정가치측정 신용손실"]
L.append("")
L.append("== seam check: prior-year 3-month column printed in the filing vs difference of two consecutive prior cumulatives (different filings)")
nb = 0; nt = 0
for lab in labs:
    q1c = S["FY2024_Q1"][lab][3]; q2 = S["FY2024_Q2"][lab]; q3 = S["FY2024_Q3"][lab]; q2c = q2[3]; q3c = q3[3]
    # Q2 prior 3mo = idx2 ; Q3 prior 3mo idx2
    for nm, three, diff in (("Q2", q2[2], q2c - q1c), ("Q3", q3[2], q3c - q2c)):
        nt += 1
        if abs(three - diff) > 1.0:  # won
            nb += 1; L.append("  SEAM DIFF %s %s printed-3mo %.0f vs cum-diff %.0f (delta %.0f won)" % (nm, lab, three, diff, three - diff))
L.append("seam compare cells %d, differing %d" % (nt, nb))
# also Q1 current 3mo vs cum equal in the filing (sanity)
q4 = S["FY2024_Q4"]
L.append("Q4: no printed 3-month column in annual filing; 2023.4Q single-quarter is cum(FY2024_Q4 FY71 col) - cum(FY2024_Q3 prior cum) -> printed pin impossible from the annual filing")
open(OUT + "v10_dangi.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
