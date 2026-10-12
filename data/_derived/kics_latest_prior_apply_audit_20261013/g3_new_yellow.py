import json, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
B = json.load(open(REPO + "/artifacts/kics_validation/report_20261012T153753Z.json", encoding="utf-8"))
A = json.load(open(REPO + "/artifacts/kics_validation/report_20261012T133013Z.json", encoding="utf-8"))
BL = {("KR0003","2023.4Q"),("KR0003","2025.1Q"),("KR0004","2023.1Q"),("KR0004","2024.1Q"),("KR0009","2023.1Q"),("KR0009","2023.2Q"),("KR0032","2024.3Q"),("KR0049","2025.1Q"),("KR0049","2026.1Q"),("KR0050","2025.3Q"),("KR0069","2024.2Q"),("KR0071","2024.4Q"),("KR0072","2025.2Q"),("KR0080","2026.1Q"),("KR0095","2024.4Q"),("KR0099","2024.3Q")}
out = open(here + "/g3_new_yellow.txt", "w", encoding="utf-8")
def idx(rep):
    d = {}
    for f in rep["findings"]:
        d[(f["원보험사코드"], f["공시분기"], f["rule"])] = f
    return d
ia, ib = idx(A), idx(B)
for k in sorted(ib, key=str):
    if (k[0], k[1]) not in BL: continue
    fa, fb = ia.get(k), ib[k]
    if fa and (fa["status"], fa.get("diff")) != (fb["status"], fb.get("diff")):
        out.write(f"{k}: {fa['status']} diff={fa.get('diff')} exp={fa.get('expected')} act={fa.get('actual')}  ->  {fb['status']} diff={fb.get('diff')} exp={fb.get('expected')} act={fb.get('actual')}\n")
# all findings in applied blocks that are not GREEN now
out.write("\n-- non-GREEN findings now in applied blocks:\n")
for k in sorted(ib, key=str):
    if (k[0], k[1]) in BL and ib[k]["status"] not in ("GREEN",):
        f = ib[k]; out.write(f"{k}: {f['status']} diff={f.get('diff')} detail={str(f.get('detail'))[:100]}\n")
