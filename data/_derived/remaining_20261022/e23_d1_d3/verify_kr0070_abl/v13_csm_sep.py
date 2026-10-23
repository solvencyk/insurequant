import sys, json
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl")
import vlib, re
ROOT = vlib.ROOT
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
W = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(ROOT + "/CSM_waterfall.json", encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
L = []
def rows(fy, start):
    for t in vlib.tables(fy):
        if t["start"] == start: return {r["cells"][0][1].strip(): [vlib.num(c[1]) for c in r["cells"][1:]] for r in t["rows"] if r["cells"]}
# which section does each copy belong to: print nearest preceding section heading
for fy, cons, sep in (("FY2024_Q1", 20300, 39850), ("FY2024_Q2", 20912, 41503), ("FY2024_Q3", 20361, 40587), ("FY2024_Q4", 26772, 55940)):
    lines = vlib.load(fy)
    def sec(n):
        for j in range(n, 0, -1):
            s = re.sub(r"<[^>]*>", "", lines[j - 1]).strip()
            if re.match(r"^(\d+\.\s*(연결)?재무제표 주석|\d+\.\s*(연결)?재무제표 *$)", s): return j, s
    a = rows(fy, cons); b = rows(fy, sep)
    L.append("%s consolidated-copy T%d section %s ; separate-copy T%d section %s ; rows identical: %s" % (fy, cons, sec(cons), sep, sec(sep), a == b))
    if a != b:
        for k in a:
            if a[k] != b.get(k): L.append("    diff %s: %s vs %s" % (k, a[k], b.get(k)))
open(OUT + "v13_csm_sep.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
