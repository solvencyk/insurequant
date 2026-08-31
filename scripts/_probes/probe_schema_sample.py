import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

rows = json.load(open("kics_disclosure.json", encoding="utf-8"))
print("kics_disclosure.json total rows:", len(rows))
print("keys:", list(rows[0].keys()))
print("sample row:")
print(json.dumps(rows[0], ensure_ascii=False, indent=2))
print()
for r in rows:
    if r.get("항목번호") == 27 and r.get("원보험사코드") == "KR0008" and r.get("공시분기") == "2026.2Q":
        print("sample item27 row (KR0008 2026.2Q):")
        print(json.dumps(r, ensure_ascii=False, indent=2))
        break

print()
bs = json.load(open("IFRS17_BS.json", encoding="utf-8"))
print("IFRS17_BS.json total rows:", len(bs))
print("keys:", list(bs[0].keys()))
print(json.dumps(bs[0], ensure_ascii=False, indent=2))

print()
# distinct 항목번호 -> 항목명 map for kics_disclosure (sorted)
items = {}
for r in rows:
    items[r["항목번호"]] = r["항목명"]
print("kics_disclosure item map (1-46):")
for k in sorted(items):
    print(f"  {k}: {items[k]}")

print()
print("distinct 원보험사코드 x 원수사명 (2026.2Q) count:")
codes = {}
for r in rows:
    if r.get("공시분기") == "2026.2Q":
        codes[r["원보험사코드"]] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))
print(len(codes))
for k in sorted(codes):
    print(f"  {k}: {codes[k]}")
