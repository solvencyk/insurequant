# -*- coding: utf-8 -*-
"""v13: life/other statement buckets - read the separate statement's prior-YTD column in full and recompute derived items."""
import sys, json, re, collections
sys.stdout.reconfigure(encoding="utf-8")
import xmlrd
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
HERE = R + "data/_derived/remaining_20261022/e21_ready25/verify/"
recs = json.load(open(HERE + "v07_cites.json", encoding="utf-8"))
master = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(R + "PL_breakdown.json", encoding="utf-8"))}
head = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.load(open(HERE + "head/PL_breakdown.json", encoding="utf-8"))}
LIFE = {"KR0104", "KR0083", "KR0070", "KR0079", "KR0068"}
# pick, per bucket, the Tier-1 statement table = the table of the item-17 / item-20 cite (not notes)
buckets = collections.defaultdict(list)
for c in recs:
    k = tuple(c["key"])
    if k[0] in LIFE:
        buckets[(k[0], k[1])].append(c)

def norm(s): return re.sub(r"\s+", "", s)

def stmt_dict(doc, t, col_idx, ncells):
    d = collections.OrderedDict()
    for r in t["rows"]:
        cs = r["cells"]
        if len(cs) == ncells and cs[0]["t"]:
            v = xmlrd.parse_num(cs[col_idx]["t"])
            if v is None and cs[col_idx]["t"].strip() in ("-", "0", ""):
                v = 0.0 if cs[col_idx]["t"].strip() in ("-", "0") else None
            d.setdefault(norm(cs[0]["t"]), []).append((cs[0]["t"], v, r["line"]))
    return d

report = []
for (co, q), cs in sorted(buckets.items()):
    # statement table: the one containing the item 20 cite
    c20 = [c for c in cs if c["key"][2] in (20, 17, 24)]
    if not c20:
        print("no statement cite", co, q); continue
    c = c20[0]
    doc = xmlrd.get(R + c["file"])
    ti, t, row, cell = xmlrd.row_at_line(doc, c["line"])
    col_idx = row["cells"].index(cell); ncells = len(row["cells"])
    unit = xmlrd.unit_div(c["unit"])
    D = stmt_dict(doc, t, col_idx, ncells)
    def g(*names, nth=0):
        for n in names:
            k = norm(n)
            if k in D and len(D[k]) > nth:
                v = D[k][nth][1]
                return None if v is None else v / unit
        return None
    def gs(prefix):
        for k, lst in D.items():
            if k.startswith(norm(prefix)): return lst[0][1] / unit if lst[0][1] is not None else None
        return None
    exp = {}
    rev = g("보험수익", "일반보험서비스수익"); rerev = g("재보험수익", "출재보험서비스수익")
    cost = g("발행한 보험계약에서 생기는 보험서비스비용", "보험비용", "일반보험서비스비용")
    recost = g("재보험비용", "출재보험서비스비용")
    if None not in (rev, cost):
        exp[3] = rev - cost
    if None not in (rerev, recost):
        exp[8] = rerev - recost
    if 3 in exp and 8 in exp:
        exp[2] = exp[3] + exp[8]
    fin_c = g("보험금융비용"); refin_c = g("재보험금융비용", "출재보험금융비용"); fin_r = g("보험금융수익"); refin_r = g("재보험금융수익", "출재보험금융수익")
    if fin_c is not None:
        exp["19a"] = -(fin_c + (refin_c or 0)) + (fin_r or 0) + (refin_r or 0)
    exp[15] = g("기타영업수익")
    print("==", co, q, c["file"].split("/")[-1], "table", t["start"], "unit", c["unit"], "colidx", col_idx, "of", ncells, "| hdr", c["chain"])
    print("   labels sample:", list(D.keys())[:12])
    for it in (1, 2, 3, 8, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 31, 32):
        m = master.get((co, q, it)); h = head.get((co, q, it)); e = exp.get(it)
        if it == 19: e = exp.get("19a")
        mark = ""
        if e is not None and m is not None and abs(e - m) > 0.0011: mark = "  <== DIFF"
        if it in (2, 3, 8, 15, 19):
            print(f"   item{it}: stmt-recomputed={e} master={m} head={h}{mark}")
    report.append((co, q))
