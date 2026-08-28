import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
rows = json.load(open("data/dart/viz/pl_breakdown_master.json", encoding="utf-8"))
for r in rows:
    if r["원보험사코드"] == "KR0083" and r["공시분기"] == "2024.3Q" and 1 <= r["항목번호"] <= 24:
        print(r["항목번호"], r["항목명"], r["값"])
