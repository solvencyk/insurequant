import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

rows = [r for r in data if r.get("원보험사코드") == "KR1000" and r.get("공시분기") == "2026.2Q"]
rows.sort(key=lambda r: r["항목번호"])
for r in rows:
    if r["항목번호"] <= 28:
        print(f"item{r['항목번호']:>2}: {r['항목명']!r:55s} 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
