# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
BEFORE = ROOT + r"\kics_disclosure.json.bak_20260901_052135_patch"
AFTER = ROOT + r"\kics_disclosure.json"

with open(BEFORE, "r", encoding="utf-8") as f:
    before = json.load(f)
with open(AFTER, "r", encoding="utf-8") as f:
    after = json.load(f)

def key(r):
    return (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))

before_idx = {key(r): r for r in before}
after_idx = {key(r): r for r in after}

print(f"before rows: {len(before)}  after rows: {len(after)}  (+{len(after)-len(before)})")

before_keys = set(before_idx)
after_keys = set(after_idx)
added_keys = after_keys - before_keys
removed_keys = before_keys - after_keys
common_keys = before_keys & after_keys

print(f"added combos: {len(added_keys)}")
for k in sorted(added_keys):
    print(f"  ADD {k}  값={after_idx[k].get('값')!r} 값_적용후={after_idx[k].get('값_적용후')!r}")

print(f"removed combos: {len(removed_keys)}")
for k in sorted(removed_keys):
    print(f"  DEL {k}")

changed = []
for k in common_keys:
    b, a = before_idx[k], after_idx[k]
    if b.get("값") != a.get("값") or b.get("값_적용후") != a.get("값_적용후") or b.get("항목명") != a.get("항목명"):
        changed.append(k)

print(f"changed existing combos: {len(changed)}")
for k in sorted(changed):
    b, a = before_idx[k], after_idx[k]
    print(f"  CHG {k}  값 {b.get('값')!r}->{a.get('값')!r}  값_적용후 {b.get('값_적용후')!r}->{a.get('값_적용후')!r}  항목명 {b.get('항목명')!r}->{a.get('항목명')!r}")

# out-of-scope check: anything not KR0029 2025.2Q/2025.3Q
scope = {("KR0029", "2025.2Q"), ("KR0029", "2025.3Q")}
outside = [k for k in (added_keys | removed_keys | set(changed)) if (k[0], k[1]) not in scope]
print(f"\nOUT-OF-SCOPE changes (not KR0029 2025.2Q/2025.3Q): {len(outside)}")
for k in sorted(outside)[:50]:
    print(f"  {k}")
