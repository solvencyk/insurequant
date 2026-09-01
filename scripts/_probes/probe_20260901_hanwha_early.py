import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
rows = json.loads(open("kics_disclosure.json", encoding="utf-8").read())
for q in ("2023.1Q","2023.2Q","2023.3Q"):
    r = next((r for r in rows if r["원보험사코드"]=="KR0002" and r["공시분기"]==q and str(r["항목번호"])=="25"), None)
    print(f"{q}: {r}")
