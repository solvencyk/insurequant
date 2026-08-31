import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

AFTER = r"C:\Users\sangwook.cho\Desktop\insurequant\artifacts\kics_validation\report_20260831T075656Z.json"
after = json.loads(open(AFTER, encoding="utf-8").read())

reds = [f for f in after["findings"] if f.get("원보험사코드") == "KR1000" and f.get("status") == "RED"]
print(f"KR1000 全분기 RED 잔존: {len(reds)}")
for f in reds:
    print(f"  {f.get('공시분기')} rule={f.get('rule')} expected={f.get('expected')} actual={f.get('actual')} diff={f.get('diff')}")
    print(f"    detail={str(f.get('detail'))[:220]}")

print()
q2 = [f for f in after["findings"] if f.get("원보험사코드")=="KR1000" and f.get("공시분기")=="2026.2Q"]
from collections import Counter
print("KR1000 2026.2Q status tally:", Counter(f.get("status") for f in q2))
