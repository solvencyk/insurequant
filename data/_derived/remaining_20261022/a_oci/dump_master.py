import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R="C:/Users/sangwook.cho/Desktop/insurequant/"
rows=json.load(open(R+"PL_breakdown.json",encoding="utf-8"))
qs=["2024.1Q","2024.2Q","2024.3Q","2024.4Q","2025.1Q","2025.2Q","2025.3Q","2025.4Q","2026.1Q","2026.2Q"]
d={}
for r in rows:
    if r["원보험사코드"]=="KR0073": d[(r["항목번호"],r["공시분기"])]=r
print("keys of a row:", sorted(next(iter(d.values())).keys()))
for it in (24,25,26,27,28,29,30,31,32):
    print(it, d[(it,"2024.4Q")]["항목명"])
    print("   값     ", [ (q, d.get((it,q),{}).get("값")) for q in qs])
    print("   당분기 ", [ (q, d.get((it,q),{}).get("값_당분기")) for q in qs])
