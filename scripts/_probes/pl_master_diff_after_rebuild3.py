import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(r"C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/c5d6e48d-e496-45b2-84e0-4e8c8bb5fb23/scratchpad")

pre = json.loads((SCRATCH / "pl_breakdown_master_PRE.json").read_text(encoding="utf-8"))
post = json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))

# positional compare
n = min(len(pre), len(post))
first_diff_idx = None
for i in range(n):
    if pre[i] != post[i]:
        first_diff_idx = i
        break
print("first positional diff idx:", first_diff_idx)
if first_diff_idx is not None:
    for j in range(max(0, first_diff_idx-2), min(n, first_diff_idx+5)):
        same = "==" if pre[j] == post[j] else "!="
        print(f"  idx {j} {same}")
        print(f"    pre : {pre[j]}")
        print(f"    post: {post[j]}")

# full multiset compare (order-independent, using json canonical string as key)
def canon(r):
    return json.dumps(r, sort_keys=True, ensure_ascii=False)

pre_set = [canon(r) for r in pre]
post_set = [canon(r) for r in post]
from collections import Counter
cpre, cpost = Counter(pre_set), Counter(post_set)
print("\nmultiset equal (order-independent, full row):", cpre == cpost)
only_pre = cpre - cpost
only_post = cpost - cpre
print("rows only in pre (as multiset):", sum(only_pre.values()))
print("rows only in post (as multiset):", sum(only_post.values()))
for s, c in list(only_pre.items())[:5]:
    print("  PRE-only:", s)
for s, c in list(only_post.items())[:5]:
    print("  POST-only:", s)
