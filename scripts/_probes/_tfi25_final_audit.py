import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

before = json.load(open("kics_disclosure.json.bak_20260901_tfi25", encoding="utf-8"))
after = json.load(open("kics_disclosure.json", encoding="utf-8"))

print(f"rows: {len(before)} -> {len(after)}  (delta {len(after)-len(before)})")

def key(r):
    return (r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기"))

before_map = {key(r): r for r in before}
after_map = {key(r): r for r in after}

before_keys = set(before_map)
after_keys = set(after_map)
added = after_keys - before_keys
removed = before_keys - after_keys
print(f"combos added: {len(added)}  removed: {len(removed)}")

# out-of-scope check: any added/removed/changed combo outside my 18 companies + 2026.2Q?
MY_CODES = {"KR0001","KR0003","KR0004","KR0011","KR0029","KR0051","KR0070","KR0072",
            "KR0080","KR0082","KR0083","KR0087","KR0094","KR0097","KR0100","KR0104",
            "KR1011","KR1098"}

oos_added = [k for k in added if not (k[0] in MY_CODES and k[2] == "2026.2Q")]
print(f"out-of-scope added combos: {len(oos_added)} {oos_added}")
print(f"removed combos (should be 0): {len(removed)} {sorted(removed)[:20]}")

changed = []
for k in before_keys & after_keys:
    b, a = before_map[k], after_map[k]
    if b != a:
        changed.append((k, b, a))
print(f"\nchanged existing rows: {len(changed)}")
oos_changed = [c for c in changed if not (c[0][0] in MY_CODES and c[0][2] == "2026.2Q")]
print(f"out-of-scope changed rows: {len(oos_changed)}")
for k, b, a in changed:
    print(f"  CHANGED {k}:")
    for field in ("값", "값_적용후"):
        if b.get(field) != a.get(field):
            print(f"    {field}: {b.get(field)!r} -> {a.get(field)!r}")

print(f"\nnew rows added ({len(added)}):")
for k in sorted(added):
    r = after_map[k]
    print(f"  {k}: 값={r.get('값')!r} 값_적용후={r.get('값_적용후')!r}")
