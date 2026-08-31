import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

AFTER = r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_20260831T075656Z.json"
after = json.loads(open(AFTER, encoding="utf-8").read())

q2 = [f for f in after["findings"] if f.get("원보험사코드")=="KR1000" and f.get("공시분기")=="2026.2Q"]
for f in q2:
    if f.get("status") in ("SKIP", "YELLOW"):
        print(f"{f.get('status'):6s} rule={f.get('rule')}")
        print(f"       detail={str(f.get('detail'))[:260]}")
