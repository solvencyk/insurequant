import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for r in data:
    if r.get("원보험사코드") == "KR1000" and r.get("공시분기") == "2026.1Q" and r.get("항목번호") in (47,48,49,50,51,52,53,54):
        print(json.dumps(r, ensure_ascii=False))
