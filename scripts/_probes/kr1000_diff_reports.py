import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
BEFORE = ROOT / "artifacts" / "kics_validation" / "report_20260831T075645Z.json"
AFTER = ROOT / "artifacts" / "kics_validation" / "report_20260831T075656Z.json"

before = json.loads(BEFORE.read_text(encoding="utf-8"))
after = json.loads(AFTER.read_text(encoding="utf-8"))

fb = before["findings"]
fa = after["findings"]
print(f"total findings: before={len(fb)} after={len(fa)}")

# key a finding by (code, quarter, rule) -- assume at most one finding per (code,quarter,rule)
def key(f):
    return (f.get("원보험사코드") or f.get("code"), f.get("공시분기") or f.get("quarter"), f.get("rule"))


kb = {key(f): f for f in fb}
ka = {key(f): f for f in fa}

all_keys = set(kb) | set(ka)
changed = []
for k in all_keys:
    a, b = kb.get(k), ka.get(k)
    sa = a.get("status") if a else None
    sb = b.get("status") if b else None
    if sa != sb:
        changed.append((k, sa, sb))

print(f"\ntotal changed (code,quarter,rule) findings: {len(changed)}")
outside = [c for c in changed if c[0][0] != "KR1000" or c[0][1] != "2026.2Q"]
print(f"changed OUTSIDE KR1000 2026.2Q: {len(outside)}")
for c in outside[:50]:
    print("  OUTSIDE-CHANGE", c)

inside = [c for c in changed if c[0][0] == "KR1000" and c[0][1] == "2026.2Q"]
print(f"\nchanged INSIDE KR1000 2026.2Q: {len(inside)}")
for k, sa, sb in sorted(inside, key=lambda x: str(x[0])):
    print(f"  {k[2]:45s} {sa} -> {sb}")

# global status tally
ca = Counter(f.get("status") for f in fa)
cbb = Counter(f.get("status") for f in fb)
print(f"\nGLOBAL before: {dict(cbb)}")
print(f"GLOBAL after:  {dict(ca)}")

# coverage census / structural gates (top-level, not in findings[])
for k in ("coverage_census", "parent_zero_child_nonzero"):
    vb = before.get(k)
    va = after.get(k)
    if vb != va:
        print(f"\n[{k}] CHANGED")
        print("  before:", json.dumps(vb, ensure_ascii=False)[:2000])
        print("  after: ", json.dumps(va, ensure_ascii=False)[:2000])
    else:
        print(f"\n[{k}] unchanged")

pci_b = before.get("parent_present_child_incomplete", {})
pci_a = after.get("parent_present_child_incomplete", {})
if pci_b != pci_a:
    print("\n[parent_present_child_incomplete] CHANGED")
    for sub in ("partial_red", "full_absent_even_review"):
        sb, sa = pci_b.get(sub, []), pci_a.get(sub, [])
        sb_set = {(r["code"], r["quarter"], r["parent_item"]) for r in sb}
        sa_set = {(r["code"], r["quarter"], r["parent_item"]) for r in sa}
        print(f"  {sub}: removed={sb_set - sa_set} added={sa_set - sb_set}")
else:
    print("\n[parent_present_child_incomplete] unchanged")

# full dump of all KR1000 2026.2Q findings, before & after, for items touching 47-54 rules
print("\n=== KR1000 2026.2Q findings mentioning rule containing tier2/tfi/47/48/49/50/51/52 ===")
watch = ("47_tier2", "48_tier2", "2_tier1_bridge", "3_tier2_composition", "50_tfi", "51_tfi")
for label, flist in (("BEFORE", fb), ("AFTER", fa)):
    print(f"-- {label} --")
    for f in flist:
        if f.get("원보험사코드") == "KR1000" and f.get("공시분기") == "2026.2Q":
            rule = f.get("rule", "")
            if any(rule.startswith(w) for w in watch):
                print(f"  rule={rule!r} status={f.get('status')} expected={f.get('expected')} "
                      f"actual={f.get('actual')} diff={f.get('diff')} detail={str(f.get('detail'))[:200]}")
