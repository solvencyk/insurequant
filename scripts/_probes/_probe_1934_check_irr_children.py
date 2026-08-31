import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open("kics_disclosure.json", encoding="utf-8") as f:
    rows = json.load(f)

targets = ["KR0004", "KR0011", "KR0029", "KR0051", "KR0068", "KR0080", "KR0087",
           "KR0094", "KR0099", "KR0100", "KR0104", "KR1098"]

for code in targets:
    by_item = {r["항목번호"]: r["값"] for r in rows
               if r["원보험사코드"] == code and r["공시분기"] == "2026.2Q" and 41 <= r["항목번호"] <= 46}
    print(code, by_item if by_item else "<ALL ABSENT>")
