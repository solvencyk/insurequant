import json, csv, sys, io
D = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/"
out = io.open(D + "e19_latest_comparative/KR0005_s1_census.txt", "w", encoding="utf-8")
def w(*a):
    out.write(" ".join(str(x) for x in a) + "\n")
rows = list(csv.DictReader(io.open(D+"d_census/d_census_table.csv", encoding="utf-8-sig")))
for r in rows:
    if r["code"] == "KR0005":
        w("=== CSV", r["quarter"])
        for k, v in r.items():
            w("  ", k, "=", v)
for fn in ["d5_buckets.json", "d6_rows.json", "d9_disposition.json", "cand_pl_cells.json", "d1_scan.json"]:
    d = json.load(io.open(D+"d_census/"+fn, encoding="utf-8"))
    w("##### ", fn, type(d).__name__, (list(d.keys())[:8] if isinstance(d, dict) else len(d)))
    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if "KR0005" in str(k) or "흥국화재" in str(k):
                    w(path + "/" + str(k), json.dumps(v, ensure_ascii=False)[:6000])
                else:
                    walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, dict) and (v.get("code") == "KR0005" or v.get("corp") == "KR0005" or "흥국화재" in str(v.get("company", ""))):
                    w(path + "[%d]" % i, json.dumps(v, ensure_ascii=False)[:6000])
                else:
                    walk(v, path + "[%d]" % i)
    walk(d, "")
out.close()
