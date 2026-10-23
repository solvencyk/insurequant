import json, re
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
L = []
for m, tag in (("PL_breakdown", "PL"), ("CSM_waterfall", "CSM")):
    rows = json.load(open(ROOT + "/" + m + ".json", encoding="utf-8"))
    names = {}
    for r in rows:
        if r["원보험사코드"] == "KR0070": names[r["항목번호"]] = r["항목명"]
    L.append("%s items: %s" % (tag, names))
open(OUT + "v04_names.txt", "w", encoding="utf-8").write("\n".join(L))
# notes of added gold entries
g = json.load(open(ROOT + "/data/_gold/user_pl_cells.json", encoding="utf-8"))
L = []
for e in g["set"]:
    if e["원보험사코드"] == "KR0070" and str(e.get("note", "")).startswith("2026-10-23"):
        n = e["note"]
        m1 = re.search(r"data/dart/\S+?\.xml L(\d+)", n)
        m2 = re.search(r"산식: (.*?)(?: 증거|$)", n)
        L.append("%s\t%s\t%s\t%s\t%s\t%s\t%s" % (e["공시분기"], e["항목번호"], e["값"], e["was"], m1.group(0) if m1 else "", m2.group(1)[:80] if m2 else "", n[n.find("경로"):n.find("경로")+60]))
open(OUT + "v04_pl_gold_pointers.tsv", "w", encoding="utf-8").write("\n".join(sorted(L)))
