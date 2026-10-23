# -*- coding: utf-8 -*-
"""Pre-load state check for KR0003 (read-only).
1. The 7 files the KB life applier wrote must equal its manifest after_sha256 (nobody touched them since), or be explained by the later fixture updates.
2. All other tracked master-ish files must equal git HEAD.
3. Print git status of tracked files and untracked files under data/_gold, tests, masters."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/apply_manifest_e23_kblife.json").read_text(encoding="utf-8"))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(args):
    p = subprocess.run(args, cwd=str(ROOT), capture_output=True, stdin=subprocess.DEVNULL)
    return p.stdout


print("== 1. KB life applier outputs vs its manifest after_sha256")
for rel, h in MAN["after_sha256"].items():
    cur = sha((ROOT / rel).read_bytes())
    print(f"  {rel}: current == after_sha256 {cur == h}")

print("== 2. tracked files equal to git HEAD (newline-normalised) or modified")
files = ["PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
         "data/_gold/gold_overlay_ledger.json", "data/_gold/pl_bridge_baseline.json", "data/_gold/pl_csm_amort_missing_ledger.json", "scripts/validate_master_tables.py", "tests/test_rule_coverage_manifest.py",
         "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json", "tests/fixtures/pl_breakdown_golden.json", "scripts/pl_breakdown/companies.py",
         "insurequant_master_tables.xlsx", "NB_CSM_multiple.json", "data/dart/viz/pl_breakdown_master.json", "data/dart/viz/csm_waterfall_master_diag.json",
         "data/_derived/pl_oci_vs_bs_aoci_warn.json", "data/_derived/qoq_warn.json"]
for rel in files:
    p = ROOT / rel
    if not p.exists():
        print(f"  {rel}: MISSING in working tree")
        continue
    head = run(["git", "show", f"HEAD:{rel}"])
    cur = p.read_bytes()
    same = cur.replace(b"\r\n", b"\n") == head.replace(b"\r\n", b"\n")
    print(f"  {rel}: {'== HEAD' if same else 'MODIFIED vs HEAD'}  size {len(cur)}")

print("== 3. git status (tracked modifications only)")
out = run(["git", "status", "--short", "--untracked-files=no"]).decode("utf-8", "replace")
print(out)
print("== 4. git diff --stat for the lane masters")
print(run(["git", "diff", "--stat", "--", "PL_breakdown.json", "CSM_waterfall.json", "data/_gold"]).decode("utf-8", "replace"))
print("== 5. branch/HEAD")
print(run(["git", "branch", "--show-current"]).decode(), run(["git", "rev-parse", "HEAD"]).decode())
