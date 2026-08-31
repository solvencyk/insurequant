"""Verify the scoped 28-company write to kics_rate_sensitivity.json touched ONLY the
intended (code, quarter) combos and left everything else byte-identical (as JSON dict
equality, key order aside).

Usage: PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
       scripts/_probes/probe_20260901_verify_28fill_diff.py
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BEFORE = Path(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_rate_sensitivity.json.bak_before_28fill")
AFTER = REPO / "kics_rate_sensitivity.json"

TOUCHED = set("""KR0001 KR0003 KR0004 KR0009 KR0011 KR0029 KR0032 KR0051 KR0068 KR0069
KR0070 KR0071 KR0072 KR0073 KR0079 KR0080 KR0082 KR0083 KR0087 KR0094
KR0097 KR0099 KR0100 KR0104 KR0150 KR1010 KR1011 KR1098""".split())

before = json.loads(BEFORE.read_text(encoding="utf-8"))
after = json.loads(AFTER.read_text(encoding="utf-8"))

KEYF = ("원보험사코드", "공시분기", "경과조치여부", "measure구분")


def key(r):
    return tuple(r.get(k) for k in KEYF)


before_by_key = {key(r): r for r in before}
after_by_key = {key(r): r for r in after}

print(f"before: {len(before)} rows / {len(before_by_key)} unique keys")
print(f"after:  {len(after)} rows / {len(after_by_key)} unique keys")

untouched_before_keys = {k for k in before_by_key if k[0] not in TOUCHED or k[1] != "2026.2Q"}
untouched_after_keys = {k for k in after_by_key if k[0] not in TOUCHED or k[1] != "2026.2Q"}
print(f"\nuntouched-scope keys: before={len(untouched_before_keys)} after={len(untouched_after_keys)}")
if untouched_before_keys != untouched_after_keys:
    print("  MISMATCH in key sets!")
    print("  missing:", untouched_before_keys - untouched_after_keys)
    print("  added:  ", untouched_after_keys - untouched_before_keys)
else:
    print("  key sets identical (OK)")

changed = []
for k in untouched_before_keys:
    if before_by_key[k] != after_by_key.get(k):
        changed.append(k)
print(f"  content changed among untouched keys: {len(changed)}")
for k in changed[:20]:
    print("   ", k)

new_2026q2 = {k for k in after_by_key if k[0] in TOUCHED and k[1] == "2026.2Q"}
print(f"\nnew 2026.2Q rows for the 28 touched companies: {len(new_2026q2)} keys")
codes_present = sorted({k[0] for k in new_2026q2})
print(f"codes represented: {len(codes_present)} -> {codes_present}")
missing_codes = sorted(TOUCHED - set(codes_present))
print(f"codes with ZERO 2026.2Q rows after this run: {missing_codes}")

print("\n=== gold file check ===")
gold_path = REPO / "data" / "_gold" / "user_rate_sensitivity_rows.json"
gold = json.loads(gold_path.read_text(encoding="utf-8"))
print(f"gold rows: {len(gold)} (expect 66, untouched by this script)")
