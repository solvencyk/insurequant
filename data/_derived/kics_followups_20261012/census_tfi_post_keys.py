"""census_tfi_post_keys.py (parser-kics, ticket 20261012T1030Z) -- READ ONLY.
How does the master express the post (값_적용후) cell of items 53/54 (and 47-52)?  Counts rows where the key is present / absent,
for the 8 reinsurers (KR1101-KR1108) vs the other 39 companies, so a new row follows the dominant convention.
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

for grp_name, pred in (("reinsurers KR1101-KR1108", lambda c: c.startswith("KR11")), ("other 39 companies", lambda c: not c.startswith("KR11"))):
    print(f"== {grp_name}")
    for it in range(47, 55):
        cnt = Counter()
        for r in rows:
            if r["항목번호"] != it or not pred(r["원보험사코드"]):
                continue
            if "값_적용후" not in r:
                cnt["key absent"] += 1
            elif r["값_적용후"] is None:
                cnt["explicit null"] += 1
            elif r["값_적용후"] == r.get("값"):
                cnt["post == pre"] += 1
            else:
                cnt["post != pre"] += 1
        print(f"  item {it}: {dict(cnt)}")

# KR1107 specifically: which rows exist for 53/54 and what is their post
print("\nKR1107 items 53/54:")
for r in rows:
    if r["원보험사코드"] == "KR1107" and r["항목번호"] in (53, 54):
        print("  ", r["공시분기"], r["항목번호"], "값=", r.get("값", "<key absent>"), "후=", r.get("값_적용후", "<key absent>"))
