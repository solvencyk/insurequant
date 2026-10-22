import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
R = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/d_census/"
rows = list(csv.DictReader(open(R + "d_census_addl.csv", encoding="utf-8-sig", newline="")))
print(list(rows[0].keys()))
for r in rows:
    if r["code"] in ("KR1000", "KR0071", "KR0069", "KR0072") and (r.get("disposition") or "") in ("STAY",) and r["quarter"] in ("2023.4Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2023.1Q", "2025.2Q"):
        print(r["code"], r["company"], r["quarter"], r.get("disposition"), "|", (r.get("disposition_reason") or r.get("cause_detail") or "")[:300].replace("\n", " "))
