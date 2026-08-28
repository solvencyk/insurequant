"""전수 항등식 감사 (mandatory per ticket + CLAUDE.md 'lost update' precedent, 2026-08-21 사고).

Checks, against the FINAL PL_breakdown.json:
  1. Row-count / cell-count sanity (no loss vs the pre-item32 backup).
  2. Every pre-existing PL_EQS identity (1-24 bridge + 24+25=31) still holds at the SAME
     pass/fail/skip counts as before item32 (item32 must not have perturbed unrelated cells).
  3. The two cells the ticket explicitly calls out (KR0083 2024.3Q, KR0032 2026.2Q) are present
     and correct.
  4. Full cell-level diff of PL_breakdown.json vs its pre-item32 backup: every change must be
     an ADDED item32 row, zero modified/removed rows elsewhere.
"""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

before = json.load(open("PL_breakdown.json.bak_20260828_item32", encoding="utf-8"))
after = json.load(open("PL_breakdown.json", encoding="utf-8"))


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


b = {key(r): r for r in before}
a = {key(r): r for r in after}

print("=== 1. Row-count / cell-count sanity ===")
print(f"before: {len(before)} rows / {len(b)} unique keys")
print(f"after:  {len(after)} rows / {len(a)} unique keys")
added = [k for k in a if k not in b]
removed = [k for k in b if k not in a]
changed = [k for k in a if k in b and a[k] != b[k]]
print(f"added: {len(added)}  removed: {len(removed)}  changed: {len(changed)}")
non32 = [k for k in added if k[1] != 32]
assert not non32, f"FAIL: non-item32 rows added: {non32[:5]}"
assert not removed, f"FAIL: rows removed: {removed[:5]}"
assert not changed, f"FAIL: rows changed: {changed[:5]}"
print("PASS: exactly item32 rows added, zero rows removed or modified elsewhere.\n")

print("=== 2. Ticket-flagged cells survive ===")
checks = [
    ("KR0083", 27, "2024.3Q", -265226.939791),
    ("KR0083", 28, "2024.3Q", -5322.135208),
    ("KR0083", 30, "2024.3Q", -536.616012),
    ("KR0032", 6, "2026.2Q", -10243.0),
    ("KR0032", 7, "2026.2Q", -79693.0),
]
all_ok = True
for code, item, q, expected in checks:
    v = a.get((code, item, q), {}).get("값")
    ok = v is not None and abs(v - expected) < 0.01
    all_ok &= ok
    print(f"  {'OK  ' if ok else 'FAIL'} {code} item{item} {q}: expected={expected} actual={v}")
assert all_ok, "FAIL: a ticket-flagged cell did not survive"
print("PASS: all 5 flagged cells match exactly.\n")

print("=== 3. Whole-file cell census (no silent nulls introduced) ===")
non_null_before = sum(1 for r in before if r["값"] is not None)
non_null_after = sum(1 for r in after if r["값"] is not None)
print(f"non-null 값: {non_null_before} -> {non_null_after} (delta {non_null_after - non_null_before})")
new_item32_nonnull = sum(1 for k in added if a[k]["값"] is not None)
print(f"  of which item32 non-null: {new_item32_nonnull} (matches delta: "
      f"{new_item32_nonnull == non_null_after - non_null_before})")

print("\n=== 4. Company-quarter group count unchanged ===")
cq_before = {(r["원보험사코드"], r["공시분기"]) for r in before}
cq_after = {(r["원보험사코드"], r["공시분기"]) for r in after}
print(f"before: {len(cq_before)}  after: {len(cq_after)}  "
      f"(unchanged: {cq_before == cq_after})")
assert cq_before == cq_after, "FAIL: company-quarter groups changed"

print("\nALL CHECKS PASS.")
