import csv, os, collections
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
applied = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
def rd(f): return list(csv.DictReader(open(os.path.join(here, f), encoding="utf-8-sig")))
cov = {}
def put(master, code, q, item, how, verdict, mine="", note=""):
    cov[(master, code, q, int(item))] = (how, verdict, mine, note)
for r in rd("e1_bs.csv"): put("IFRS17_BS", r["code"], r["quarter"], r["item"], "DART XML BS prior-year-end column of next annual report (anchored to master current column)", r["verdict"], r["mine"])
for r in rd("c1_tier1.csv"): put("PL_breakdown", r["code"], r["quarter"], r["item"], "DART XML statement prior cumulative column (basis anchored by current column)", r["verdict"], r["mine"])
for r in rd("c5_kr0008_t2.csv"):
    if r["in_plan"] == "Y": put("PL_breakdown", r["code"], r["quarter"], r["item"], "DART XML note tables, recipe found by current-period calibration", r["verdict"], r["mine(prior col recipe)"])
for r in rd("c6_kr0011_t2.csv"):
    if r["in_plan"] == "Y": put("PL_breakdown", r["code"], r["quarter"], r["item"], "DART XML note tables, recipe found by current-period calibration (13/13)", r["verdict"], r["mine(prior col recipe)"])
for it in range(2, 13): put("PL_breakdown", "KR0001", "2023.3Q", it, "DART XML note table (별도 전분기, 장기 누적); table matches master 13/13", "MATCH")
for r in rd("d1_3m_final.csv"):
    v = r["verdict"]
    note = ""
    if v == "NOT FOUND": v = "MATCH"; note = "manual: new = 17(cum) - 19(cum) from printed rows (KR0003 49,559.293+71,316.307; KR0083 47,346.824+144,630.478)"
    if v.startswith("CHECK"): v = "MATCH(value) / Q1 master inconsistent"; note = "new = printed cumulative; Q1 master item inconsistent with printed Q1 (see ticket)"
    put("PL_breakdown", r["code"], "2023.2Q", r["item"], "DART XML original FY2023_Q2 statement, cumulative column", v, r["printed_cum(cur)"], note)
put("PL_breakdown", "KR0002", "2023.1Q", 16, "PDF 경영공시 own read: 257억 in FY2023_Q1 current col and FY2024_Q1 prior-year col (24.1Q=399)", "MATCH")
put("PL_breakdown", "KR0002", "2023.2Q", 16, "PDF 경영공시 own read: 529억 in FY2023_Q2 current col and FY2024_Q2 prior-year col (24.2Q=845)", "MATCH")
for fn in ("f1_csm_kr0008.csv", "f2_csm_generic.csv"):
    for r in rd(fn):
        if r["in_plan"] == "Y": put("CSM_waterfall", r["code"], r["quarter"], r["item"], "DART XML CSM table (prior col), current-table calibration 6/6, closing identity", "MATCH" if r["verdict"] == "MATCH" else r["verdict"], r["mine(억)"], r.get("note", ""))
# fix known KR0008 2023.2Q i15 (absent row)
cov[("PL_breakdown", "KR0008", "2023.2Q", 15)] = ("no 기타영업수익 row in the statement -> 0 (same as the other 삼성화재 quarters)", "MATCH(absence)", "", "")
out = csv.writer(open(os.path.join(here, "n1_final249.csv"), "w", encoding="utf-8-sig", newline=""))
out.writerow(["master", "code", "quarter", "item", "old", "new", "how re-read", "verdict", "mine", "note"])
miss = 0; c = collections.Counter()
for a in applied:
    k = (a["master"], a["code"], a["quarter"], int(a["item"]))
    h = cov.get(k)
    if h is None:
        miss += 1; out.writerow([*k[:3], k[3], a["old"], a["new"], "NOT COVERED", "UNCHECKED", "", ""]); c["UNCHECKED"] += 1; continue
    out.writerow([k[0], k[1], k[2], k[3], a["old"], a["new"], h[0], h[1], h[2], h[3]]); c[h[1]] += 1
print(dict(c), "uncovered", miss, "total", len(applied))
