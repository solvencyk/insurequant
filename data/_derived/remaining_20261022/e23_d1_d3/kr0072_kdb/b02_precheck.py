# -*- coding: utf-8 -*-
"""KR0072 KDB precheck (read-only): the live masters/gold/tests are exactly the state after the ABL load of this chain
(sha256 == kr0070_abl/apply_manifest_e23_abl.json after_sha256), and everything else vs git HEAD is only what earlier agents of THIS workflow changed."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
sys.stdout.reconfigure(encoding="utf-8")


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


man = json.loads((EV / "kr0070_abl/apply_manifest_e23_abl.json").read_text(encoding="utf-8"))
ok = True
for rel, h in man["after_sha256"].items():
    cur = sha(rel)
    same = cur == h
    ok = ok and same
    print(f"{rel}: live == ABL after_sha256 {same}")

# other files that the earlier chain steps touched (compare with their documented states)
for rel in ["data/_gold/gold_overlay_ledger.json", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
            "tests/fixtures/pl_breakdown_golden.json", "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json",
            "insurequant_master_tables.xlsx", "NB_CSM_multiple.json", "data/dart/viz/pl_breakdown_master.json", "scripts/pl_breakdown/companies.py"]:
    p = ROOT / rel
    if not p.exists():
        print(rel, "MISSING")
        continue
    cur = sha(rel)
    r = subprocess.run(["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--", rel], capture_output=True)
    print(f"{rel}: sha256 {cur[:16]} | differs from git HEAD: {r.returncode != 0}")
print("ALL OK" if ok else "MISMATCH")
