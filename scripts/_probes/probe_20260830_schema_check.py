import sys, json
sys.stdout.reconfigure(encoding="utf-8")

GOLD_PATH = "data/_gold/user_csm_cells.json"

d = json.load(open(GOLD_PATH, encoding="utf-8"))
s = d["set"]
print("first 3 entries:")
for e in s[:3]:
    print(json.dumps(e, ensure_ascii=False))
