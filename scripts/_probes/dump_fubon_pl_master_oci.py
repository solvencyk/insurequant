import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

d = json.load(open("PL_breakdown.json", encoding="utf-8"))
rows = [r for r in d if r["원보험사코드"] == "KR0083" and r["공시분기"] == "2024.3Q" and r["항목번호"] in range(24, 32)]
rows.sort(key=lambda r: r["항목번호"])
for r in rows:
    print(f"item{r['항목번호']:>2} {r['항목명']:<12}  값(누적)={r['값']:>15,.3f}  값_당분기={r['값_당분기']:>15,.3f}")

print()
sub = next((r["값"] for r in rows if r["항목번호"] == 25), None)
comps = [next((r["값"] for r in rows if r["항목번호"] == i), None) for i in range(26, 31)]
print("subtotal(item25) 누적:", sub)
print("comps(26-30) 누적:", comps)
if all(c is not None for c in comps):
    print("sum comps:", sum(comps))
    print("residual:", sub - sum(comps))

sub_q = next((r["값_당분기"] for r in rows if r["항목번호"] == 25), None)
comps_q = [next((r["값_당분기"] for r in rows if r["항목번호"] == i), None) for i in range(26, 31)]
print("\nsubtotal(item25) 당분기:", sub_q)
print("comps(26-30) 당분기:", comps_q)
if all(c is not None for c in comps_q):
    print("sum comps_q:", sum(comps_q))
    print("residual_q:", sub_q - sum(comps_q))
