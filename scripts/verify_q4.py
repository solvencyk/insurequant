"""Quick check of what 2025.4Q content actually landed in kics_disclosure.json."""
import json
from collections import defaultdict

with open(r"C:\Users\sangwook.cho\Desktop\solvency\kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

q4_companies: dict[str, list[dict]] = defaultdict(list)
for r in data:
    if r["공시분기"] == "2025.4Q":
        q4_companies[r["원보험사코드"]].append(r)

print(f"Total 2025.4Q rows: {sum(len(v) for v in q4_companies.values())}")
print(f"Companies with at least 1 2025.4Q row: {len(q4_companies)}")
print()
print("Per-company row counts:")
for code in sorted(q4_companies):
    print(f"  {code}: {len(q4_companies[code])} rows")
print()
print("Companies with 0 rows (PDF parse failed):")
for c in ("KR0010", "KR0079", "KR0080"):
    print(f"  {c}: {len(q4_companies.get(c, []))}")
print()
print("Sample (KR0001 메리츠화재 가/나/다):")
for r in data:
    if (
        r["원보험사코드"] == "KR0001"
        and r["공시분기"] == "2025.4Q"
        and r["항목명"].startswith(("가", "나", "다"))
    ):
        print(f"  {r['항목명']} = {r['값']}")
print()
print("Sample (KR0068 한화생명 가/나/다):")
for r in data:
    if (
        r["원보험사코드"] == "KR0068"
        and r["공시분기"] == "2025.4Q"
        and r["항목명"].startswith(("가", "나", "다"))
    ):
        print(f"  {r['항목명']} = {r['값']}")
