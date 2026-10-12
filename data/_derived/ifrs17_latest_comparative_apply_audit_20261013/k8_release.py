import json, os
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
def L(f): return json.load(open(REPO + "/" + f, encoding="utf-8"))
pl = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): float(r["값"]) for r in L("PL_breakdown.json") if r.get("값") not in (None, "")}
cs = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): float(r["값"]) for r in L("CSM_waterfall.json") if r.get("값") not in (None, "")}
out = open(here + "/k8_release.txt", "w", encoding="utf-8")
def g(code, q, it): return pl.get((code, q, it), 0.0)
out.write("(a) 보험손익(dual): item1 vs [bare] i2+i13+i14 and [adj] i2+i13+i14+i15-i16 (백만원; tol max(0.1%,200))\n")
for name, code, q in (("DB손보", "KR0011", "2023.1Q"), ("DB손보", "KR0011", "2023.2Q"), ("DB손보", "KR0011", "2023.3Q"), ("메리츠", "KR0001", "2023.3Q")):
    i1 = g(code, q, 1); bare = g(code, q, 2) + g(code, q, 13) + g(code, q, 14); adj = bare + g(code, q, 15) - g(code, q, 16)
    tol = max(abs(i1) * 0.001, 200.0)
    out.write(f"   {name} {q}: item1={i1:.1f} bare={bare:.1f} (d {i1-bare:.1f}) adj={adj:.1f} (d {i1-adj:.1f}) tol={tol:.1f} -> {'CLOSES' if min(abs(i1-bare), abs(i1-adj)) <= tol else 'OPEN'}\n")
out.write("(b) 세전이익 = 영업이익 + 영업외손익\n")
for name, code in (("한화생명", "KR0068"), ("한화손보", "KR0002")):
    q = "2023.2Q"
    i22 = g(code, q, 22); s = g(code, q, 20) + g(code, q, 21); tol = max(abs(i22) * 0.001, 200.0)
    out.write(f"   {name} {q}: item22={i22:.3f} item20+21={s:.3f} diff {i22-s:.3f} tol {tol:.1f} -> {'CLOSES' if abs(i22-s) <= tol else 'OPEN'}\n")
out.write("(c) DB손보 CSM상각: PL i4 (원수CSM상각, 백만원 -> 억) vs waterfall |i5| (억)\n")
for q in ("2023.1Q", "2023.2Q", "2023.3Q"):
    p4 = g("KR0011", q, 4) / 100.0; w5 = abs(cs.get(("KR0011", q, 5), 0.0))
    rel = abs(p4 - w5) / max(w5, 1e-9)
    out.write(f"   {q}: PL {p4:.2f}억 waterfall {w5:.2f}억 residual {p4-w5:.2f}억 rel {rel:.5f} -> {'CLOSES' if abs(p4-w5) <= max(5.0, 0.01*w5) else 'OPEN'}\n")
out.write("(d) 농협생명 FY2023: opening CSM (item 1) equal across 2023.1Q-4Q: " + str([cs.get(("KR0104", q, 1)) for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q")]) + "\n")
out.write("    and 2024.1Q opening (= 2023.4Q closing): " + str((cs.get(("KR0104", "2024.1Q", 1)), cs.get(("KR0104", "2023.4Q", 6)))) + "\n")
