import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SCRATCH = Path(r"C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/c5d6e48d-e496-45b2-84e0-4e8c8bb5fb23/scratchpad")

pre = json.loads((SCRATCH / "pl_breakdown_master_PRE.json").read_text(encoding="utf-8"))
post = json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))

def key(r):
    return (str(r["원보험사코드"]), str(r["공시분기"]), str(r["항목번호"]))

pre_map = {key(r): r["값"] for r in pre}
post_map = {key(r): r["값"] for r in post}

diffs = []
for k in (set(pre_map) & set(post_map)):
    a, b = pre_map[k], post_map[k]
    if a != b:
        diffs.append((k, a, b))

print(f"value diffs: {len(diffs)}")
for k, a, b in sorted(diffs, key=lambda x: x[0]):
    print(f"  {k}: {a!r} -> {b!r}")

# also check field-level diffs beyond 값 (in case row order or other fields differ)
import hashlib
print("\nraw bytes equal:", (SCRATCH / "pl_breakdown_master_PRE.json").read_bytes() == (ROOT / "data/dart/viz/pl_breakdown_master.json").read_bytes())
