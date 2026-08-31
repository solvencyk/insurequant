import sys, json
sys.stdout.reconfigure(encoding="utf-8")

GOLD_PATH = "data/_gold/user_csm_cells.json"

d = json.load(open(GOLD_PATH, encoding="utf-8"))
s = d["set"]
keys = set()
for e in s:
    keys.update(e.keys())
print("all keys used across set:", sorted(keys))

# find entries that DO have why/note (whatever key name)
for k in ["why", "note", "이유", "비고", "출처", "근거"]:
    cnt = sum(1 for e in s if e.get(k))
    print(f"key={k!r} non-empty count={cnt}")
