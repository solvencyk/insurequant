import json, os, collections
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(REPO + "/artifacts/kics_validation/report_20261012T133013Z.json", encoding="utf-8"))
B = json.load(open(REPO + "/artifacts/kics_validation/report_20261012T153753Z.json", encoding="utf-8"))
out = open(here + "/g2_gate_diff.txt", "w", encoding="utf-8")
def m(rep):
    c = collections.Counter()
    for f in rep["findings"]:
        c[(f["원보험사코드"], f["공시분기"], f["rule"], f["status"])] += 1
    return c
ma, mb = m(A), m(B)
out.write(f"findings old={len(A['findings'])} new={len(B['findings'])}; matrix keys old={len(ma)} new={len(mb)}\n")
rem = ma - mb; add = mb - ma
out.write(f"matrix entries removed (in old not new): {sum(rem.values())}; added (in new not old): {sum(add.values())}\n")
BLOCKS = {("KR0003","2023.4Q"),("KR0003","2025.1Q"),("KR0004","2023.1Q"),("KR0004","2024.1Q"),("KR0009","2023.1Q"),("KR0009","2023.2Q"),("KR0032","2024.3Q"),("KR0049","2025.1Q"),("KR0049","2026.1Q"),("KR0050","2025.3Q"),("KR0069","2024.2Q"),("KR0071","2024.4Q"),("KR0072","2025.2Q"),("KR0080","2026.1Q"),("KR0095","2024.4Q"),("KR0099","2024.3Q")}
out.write("--- removed:\n")
for k, v in sorted(rem.items(), key=str):
    out.write(f"  {k} x{v} {'[in applied block]' if (k[0],k[1]) in BLOCKS else '[OUTSIDE applied blocks]'}\n")
out.write("--- added:\n")
for k, v in sorted(add.items(), key=str):
    out.write(f"  {k} x{v} {'[in applied block]' if (k[0],k[1]) in BLOCKS else '[OUTSIDE applied blocks]'}\n")
def reds(rep): return sorted((f["원보험사코드"], f["공시분기"], f["rule"]) for f in rep["findings"] if f["status"] == "RED")
out.write(f"RED old={len(reds(A))} new={len(reds(B))}\n")
out.write(f"summary old={A['summary']} new={B['summary']}\n")
