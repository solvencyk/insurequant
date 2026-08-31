import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    rows = json.load(f)

for r in rows:
    if r["원보험사코드"] == "KR1098" and r["공시분기"] == "2026.2Q" and 36 <= r["항목번호"] <= 40:
        print(r)

print("count matched:", sum(1 for r in rows if r["원보험사코드"] == "KR1098" and r["공시분기"] == "2026.2Q" and 36 <= r["항목번호"] <= 40))
