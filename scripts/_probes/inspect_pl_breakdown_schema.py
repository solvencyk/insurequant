import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

d = json.load(open("PL_breakdown.json", encoding="utf-8"))
print("n records:", len(d))
print("sample record:")
print(json.dumps(d[0], ensure_ascii=False, indent=2)[:2000])

# find distinct item numbers / names
items = {}
for r in d:
    items[r.get("item_no") if "item_no" in r else None] = r.get("item_name") if "item_name" in r else None

print("\nkeys of sample record:", list(d[0].keys()))
