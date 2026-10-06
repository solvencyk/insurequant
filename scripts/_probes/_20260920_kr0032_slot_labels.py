"""Print the EXACT stored (항목번호, 항목명, 값, 값_적용후) for KR0032 items 4-13,
per quarter, so we can see whether the label travelled with the value."""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(ROOT, "kics_disclosure.json"), encoding="utf-8") as f:
    kics = json.load(f)

CODE = "KR0032"
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.3Q", "2024.4Q", "2025.1Q"]

for q in QS:
    print("=" * 84)
    print(f"### {CODE}  {q}")
    rows = [r for r in kics
            if r.get("원보험사코드") == CODE and r.get("공시분기") == q
            and 4 <= int(r["항목번호"]) <= 13]
    rows.sort(key=lambda r: int(r["항목번호"]))
    for r in rows:
        print(f"  item{int(r['항목번호']):>3}  값={str(r.get('값')):>10}  "
              f"후={str(r.get('값_적용후')):>10}  항목명='{r.get('항목명')}'")

# Cross-company: does any OTHER company also carry a 조정준비금-style shift?
print()
print("=" * 84)
print("### Cross-company scan: companies whose item10 (비지배지분 slot) label is NOT 비지배지분")
seen = {}
for r in kics:
    if int(r["항목번호"]) in (7, 8, 9, 10, 11):
        key = (int(r["항목번호"]), r.get("항목명"))
        seen.setdefault(key, set()).add((r.get("원보험사코드"), r.get("공시분기")))
for (it, lab), who in sorted(seen.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
    print(f"  item{it:>3}  n={len(who):>4}  label='{lab}'")
