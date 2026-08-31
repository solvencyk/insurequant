import json
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

disc = json.load(open("kics_disclosure.json", encoding="utf-8"))

# find any rows with items 36-46 to see label convention + whether 값_적용후 populated
rows_36_46 = [r for r in disc if r.get("항목번호") in range(36, 47)]
print(f"Total rows items 36-46 across dataset: {len(rows_36_46)}")

# distinct labels per item number
from collections import defaultdict
labels = defaultdict(set)
has_post = defaultdict(int)
no_post = defaultdict(int)
for r in rows_36_46:
    labels[r["항목번호"]].add(r["항목명"])
    if r.get("값_적용후") is not None:
        has_post[r["항목번호"]] += 1
    else:
        no_post[r["항목번호"]] += 1

for n in range(36, 47):
    print(f"\nitem{n}: labels={labels.get(n)}")
    print(f"  has 값_적용후: {has_post.get(n,0)}, missing 값_적용후: {no_post.get(n,0)}")

# Sample a few full rows for item 36 and item 41 to see complete structure
print("\n=== sample item36 rows (first 3) ===")
for r in [r for r in rows_36_46 if r["항목번호"] == 36][:3]:
    print(r)

print("\n=== sample item41 rows (first 3) ===")
for r in [r for r in rows_36_46 if r["항목번호"] == 41][:3]:
    print(r)

# Also check KR0049's own earlier even-Q quarters (2024.2Q, 2024.4Q, 2025.2Q, 2025.4Q) for items 36-46
print("\n=== KR0049 own history items 36-46 ===")
kr0049_3646 = [r for r in disc if r.get("원보험사코드") == "KR0049" and r.get("항목번호") in range(36, 47)]
kr0049_3646.sort(key=lambda r: (r["공시분기"], r["항목번호"]))
for r in kr0049_3646:
    print(r["공시분기"], r["항목번호"], r["항목명"], "값=", r.get("값"), "적용후=", r.get("값_적용후"))
