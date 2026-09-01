# -*- coding: utf-8 -*-
"""Diff two capital_securities_fy2026h1.json snapshots: confirm outstanding_mn/face_amount_mn
never changed for any bond that existed in both (only as_of/source_file/name should move)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
before_path, after_path = sys.argv[1], sys.argv[2]
before = json.loads(Path(before_path).read_text(encoding="utf-8"))
after = json.loads(Path(after_path).read_text(encoding="utf-8"))

b_by_code = {c["code"]: c for c in before["companies"]}
a_by_code = {c["code"]: c for c in after["companies"]}
assert set(b_by_code) == set(a_by_code), "company set changed!"

amount_diffs = []
asof_changes = []
for code in b_by_code:
    bb, aa = b_by_code[code]["bonds"], a_by_code[code]["bonds"]
    # key by (tier, issue_date) since names can get annotated
    def key(b):
        return (b["tier"], b.get("issue_date"), b.get("face_amount_mn"))
    b_by_key = {}
    for b in bb:
        b_by_key.setdefault((b["tier"], b.get("issue_date")), []).append(b)
    a_by_key = {}
    for b in aa:
        a_by_key.setdefault((b["tier"], b.get("issue_date")), []).append(b)
    for k in set(b_by_key) & set(a_by_key):
        blist, alist = b_by_key[k], a_by_key[k]
        if len(blist) == 1 and len(alist) == 1:
            b1, a1 = blist[0], alist[0]
            if b1.get("outstanding_mn") != a1.get("outstanding_mn") or b1.get("face_amount_mn") != a1.get("face_amount_mn"):
                amount_diffs.append((code, k, b1.get("outstanding_mn"), a1.get("outstanding_mn"),
                                     b1.get("face_amount_mn"), a1.get("face_amount_mn")))
            if b1.get("as_of") != a1.get("as_of"):
                asof_changes.append((code, k, b1.get("as_of"), a1.get("as_of")))

print(f"AMOUNT DIFFS (should be empty): {len(amount_diffs)}")
for d in amount_diffs:
    print(f"  {d}")
print(f"\nAS_OF CHANGES (expected, listing): {len(asof_changes)}")
for d in sorted(asof_changes):
    print(f"  {d}")
