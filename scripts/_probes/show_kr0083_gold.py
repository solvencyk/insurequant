import json
import sys
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("data/_gold/user_pl_cells.json", encoding="utf-8"))
for s in d.get("set", []):
    if s["원보험사코드"] == "KR0083":
        print(s["항목번호"], s["공시분기"], s["값"], "was:", s.get("was"))
