# -*- coding: utf-8 -*-
"""Pre-load backup of every file this load (KDB KR0072, D3, load 2) can touch.  Copies under data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2/<same relative path> and writes
SHA256_preload.txt.  Refuses to run when the live files are NOT the state after the Hyundai load of this chain (six data files == kr0009_hyundai/apply_manifest_e23_hd.json after_sha256) plus the validation
cleanup copies (test file / golden fixture == gate_cleanup/post_copies), unless --force-record is given.  Backups are never overwritten with different bytes."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
BK = EV / "backup_before_apply/kr0072_kdb_load2"
sys.stdout.reconfigure(encoding="utf-8")
FILES = ["PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
         "data/_gold/gold_overlay_ledger.json", "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
         "tests/fixtures/pl_breakdown_golden.json", "tests/fixtures/viz_ifrs17_panels_golden.json", "tests/fixtures/viz_csm_waterfall_golden.json",
         "data/_derived/pl_oci_vs_bs_aoci_warn.json", "data/_derived/qoq_warn.json", "data/dart/viz/csm_continuity_validation.json", "NB_CSM_multiple.json", "data/dart/viz/pl_breakdown_master.json",
         "scripts/validate_master_tables.py"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


man = json.loads((EV / "kr0009_hyundai/apply_manifest_e23_hd.json").read_text(encoding="utf-8"))
bad = [rel for rel, h in man["after_sha256"].items() if not rel.startswith("tests/") and sha(ROOT / rel) != h]
GC = EV / "gate_cleanup/post_copies"
for rel, name in (("tests/test_rule_coverage_manifest.py", "test_rule_coverage_manifest.py"), ("tests/fixtures/master_tables_golden.json", "master_tables_golden.json"),
                  ("scripts/validate_master_tables.py", "validate_master_tables.py")):
    if sha(ROOT / rel) != sha(GC / name):
        bad.append(rel)
if bad and "--force-record" not in sys.argv:
    raise SystemExit(f"ABORT: live files are not the post-Hyundai + validation-cleanup state: {bad}")
lines = []
for rel in FILES:
    src, dst = ROOT / rel, BK / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and sha(dst) != sha(src):
        raise SystemExit(f"ABORT: backup {dst} exists and differs from the live file (somebody changed it since the first backup)")
    shutil.copyfile(src, dst)
    assert sha(dst) == sha(src)
    lines.append(f"{sha(src)} *{rel}")
    print("backed up", rel, sha(src)[:16])
(BK / "SHA256_preload.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("done", len(FILES), "files ->", BK)
