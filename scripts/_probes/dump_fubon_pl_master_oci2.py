import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

d = json.load(open("PL_breakdown.json", encoding="utf-8"))
rows = [r for r in d if r["원보험사코드"] == "KR0083" and r["공시분기"] == "2024.3Q" and r["항목번호"] in range(24, 32)]
rows.sort(key=lambda r: r["항목번호"])
by_item = {r["항목번호"]: r for r in rows}
for i in range(24, 32):
    r = by_item.get(i)
    if r is None:
        print(f"item{i:>2}  MISSING (no record at all)")
        continue
    v = r["값"]
    vq = r["값_당분기"]
    vs = f"{v:,.3f}" if v is not None else "None"
    vqs = f"{vq:,.3f}" if vq is not None else "None"
    print(f"item{i:>2} {r['항목명']:<14}  값(누적)={vs:>15}  값_당분기={vqs:>15}")

comps_q = [by_item[i]["값_당분기"] for i in range(26, 31) if i in by_item]
print("\ncomps_q raw:", comps_q)
present = [c for c in comps_q if c is not None]
print("sum of present 당분기 comps:", sum(present) if present else None)
sub_q = by_item[25]["값_당분기"]
print("subtotal 당분기:", sub_q)
