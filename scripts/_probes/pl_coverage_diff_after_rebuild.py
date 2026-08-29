import json
import sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(r"C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/c5d6e48d-e496-45b2-84e0-4e8c8bb5fb23/scratchpad")

pre = json.loads((SCRATCH / "pl_breakdown_coverage_PRE.json").read_text(encoding="utf-8"))
post = json.loads((ROOT / "data/_derived/pl_breakdown_coverage.json").read_text(encoding="utf-8"))
print("pre len", len(pre), "post len", len(post))

def canon(r):
    return json.dumps(r, sort_keys=True, ensure_ascii=False)

cpre, cpost = Counter(canon(r) for r in pre), Counter(canon(r) for r in post)
print("multiset equal:", cpre == cpost)
only_pre = cpre - cpost
only_post = cpost - cpre
print("only in pre:", sum(only_pre.values()), "only in post:", sum(only_post.values()))
for s in list(only_pre)[:10]:
    print("  PRE-only:", s)
for s in list(only_post)[:10]:
    print("  POST-only:", s)

# positional
n = min(len(pre), len(post))
first_diff = next((i for i in range(n) if pre[i] != post[i]), None)
print("first positional diff idx:", first_diff)

# find where KR0001/2023.1Q sits in pre master, item32 specifically, to explain the ordering quirk
master_pre = json.loads((SCRATCH / "pl_breakdown_master_PRE.json").read_text(encoding="utf-8"))
for i, r in enumerate(master_pre):
    if r["원보험사코드"] == "KR0001" and r["공시분기"] == "2023.1Q" and r["항목번호"] == 32:
        print(f"\nKR0001 2023.1Q item32 sits at index {i} in PRE (out of {len(master_pre)})")
        break
else:
    print("\nKR0001 2023.1Q item32 NOT FOUND in PRE master")
# what's immediately around that index?
for j in range(max(0,i-1), i+2):
    print(f"  idx {j}: {master_pre[j]}")
