import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

bs = json.load(open("IFRS17_BS.json", encoding="utf-8"))
seen = {}
for r in bs:
    key = (r["항목번호"], r["항목명"], r["섹션"], r["레벨"])
    seen[key] = seen.get(key, 0) + 1
print("distinct (항목번호,항목명,섹션,레벨) combos:")
for k in sorted(seen):
    print(f"  {k}  n={seen[k]}")

print()
print("distinct 공시분기 values (sorted):")
qs = sorted({r["공시분기"] for r in bs})
print(qs)
print("count:", len(qs))

print()
# how KR0150 (서울보증) and KR0087 (동양) appear across masters
for code in ("KR0150", "KR0087"):
    n = sum(1 for r in bs if r["원보험사코드"] == code)
    quarters = sorted({r["공시분기"] for r in bs if r["원보험사코드"] == code})
    print(f"{code} in IFRS17_BS: rows={n} quarters={quarters}")

kd = json.load(open("kics_disclosure.json", encoding="utf-8"))
for code in ("KR0150", "KR0087"):
    n = sum(1 for r in kd if r["원보험사코드"] == code)
    quarters = sorted({r["공시분기"] for r in kd if r["원보험사코드"] == code})
    print(f"{code} in kics_disclosure: rows={n} quarters={quarters}")
