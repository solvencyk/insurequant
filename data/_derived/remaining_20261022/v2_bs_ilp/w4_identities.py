"""Closure checks on the working masters for KR0073: BS identity, 20<=2, ILP 10+14=15, ILP15==BS20/100, RE roll, PL net income."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
bs = json.load(open(R + "IFRS17_BS.json", encoding="utf-8"))
ilp = json.load(open(R + "insurance_liability_portfolio.json", encoding="utf-8"))
pl = json.load(open(R + "PL_breakdown.json", encoding="utf-8"))
def b(q, i):
    for r in bs:
        if r["원보험사코드"] == "KR0073" and r["공시분기"] == q and r["항목번호"] == i: return r["값"]
def l(q, i):
    for r in ilp:
        if r["원보험사코드"] == "KR0073" and r["공시분기"] == q and r["항목번호"] == i: return r["값"]
for q in ["2023.4Q", "2024.4Q", "2025.4Q"]:
    A, L, E, B20, RE = b(q, 1), b(q, 2), b(q, 3), b(q, 20), b(q, 31)
    print(q, "1-2-3 =", round(A - L - E, 6), "| 20 <= 2:", B20 <= L, "| item20", B20, "RE", RE)
q = "2023.4Q"
print("ILP 10+14-15 =", round(l(q, 10) + l(q, 14) - l(q, 15), 6), "| 15 - BS20/100 =", round(l(q, 15) - b(q, 20) / 100, 6), "| 13", l(q, 13), "10", l(q, 10))
print("RE roll (mn):", 5920420.191959 + 632200.607207 - 51250 - 74244.916670, "vs master 31", b(q, 31))
print("equity roll check: opening after changes 5920420.191959 vs master?")
# PL net income FY2023
names = {}
for r in pl[:0]: pass
sample = [r for r in pl if r.get("원보험사코드") == "KR0073" and r.get("공시분기") == "2023.4Q"]
print("PL rows KR0073 2023.4Q:", len(sample))
for r in sample:
    nm = r.get("항목명", "")
    if "당기순이익" in nm or "법인세" in nm:
        print(r.get("항목번호"), nm, r.get("값"), r.get("값_적용후") if "값_적용후" in r else "")
# other quarters: quarter-by-quarter equity=3 sanity, count other Kyobo quarters with 1-2-3 residual
for qq in sorted({r["공시분기"] for r in bs if r["원보험사코드"] == "KR0073"}):
    A, L, E = b(qq, 1), b(qq, 2), b(qq, 3)
    if None not in (A, L, E):
        print(qq, "residual 1-2-3:", round(A - L - E, 3))
