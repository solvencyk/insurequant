import json, sys
sys.stdout.reconfigure(encoding="utf-8")
import fitz
pl = json.load(open("PL_breakdown.json", encoding="utf-8"))
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    print(q, [(r["항목번호"], r["항목명"], r["값"], r.get("값_당분기")) for r in pl if r["원보험사코드"]=="KR1102" and r["공시분기"]==q and str(r["항목번호"]) in ("1","16","22","23","24")])
d = fitz.open("data/disclosure/FY2023_Q2/raw/KR1102_스위스리아시아.pdf")
print(d[4].get_text())
