# -*- coding: utf-8 -*-
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    rows = json.load(f)

matches = [r for r in rows if r.get("원보험사코드") == "KR0075" and r.get("공시분기") == "2024.3Q" and r.get("항목번호") in {3,47,48,49,50,51}]
matches.sort(key=lambda r: r.get("항목번호", 0))
for r in matches:
    print(f"  item{r.get('항목번호'):>3} {r.get('항목명','')[:28]:28s} val={r.get('값')!r:>14} post={r.get('값_적용후')!r:>14}")

v47 = float([r for r in matches if r["항목번호"]==47][0]["값"])
v49 = float([r for r in matches if r["항목번호"]==49][0]["값"])
v51 = float([r for r in matches if r["항목번호"]==51][0]["값"])
gap = v51 - v47
print(f"\ngap(item51-item47) = {gap:.2f}, ratio to item49 = {gap/v49*100:.1f}%")
