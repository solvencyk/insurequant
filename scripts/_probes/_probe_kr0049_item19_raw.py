import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

disc = json.load(open("kics_disclosure.json", encoding="utf-8"))
for r in disc:
    if r.get("원보험사코드") == "KR0049" and r.get("공시분기") == "2026.2Q" and r.get("항목번호") == 19:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print("types: 값=", type(r.get("값")), " 값_적용후=", type(r.get("값_적용후")))
