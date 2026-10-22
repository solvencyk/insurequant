import json, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_READY_all.json", encoding="utf-8").read())
T2 = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}
cnt = Counter(); per = defaultdict(Counter)
for c in d["pl_cells"]:
    k = "T2" if c["item"] in T2 else "T1"
    cnt[k] += 1
    per[c["code"]][k] += 1
print(cnt)
for co, v in sorted(per.items()):
    print(co, dict(v))
print(Counter(c["item"] for c in d["pl_cells"] if c["item"] in T2))
print("gold overlap cells:", [(c["code"], c["q"], c["item"], c["gold"], c["new"]) for c in d["pl_cells"] if c.get("gold") is not None])
print("old None (fills):", sum(1 for c in d["pl_cells"] if c["old"] is None), "of", len(d["pl_cells"]))
