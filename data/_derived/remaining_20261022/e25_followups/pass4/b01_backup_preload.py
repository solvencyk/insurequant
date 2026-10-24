# -*- coding: utf-8 -*-
"""Copy every file this batch (pass4, ticket 20261024T1000Z) may change into backup_before_apply/<repo-relative path> BEFORE the first write and prove the copies are byte-identical (sha256 of source == sha256 of copy
== sha256 recorded in git HEAD where the file is tracked and unmodified).  Writes backup_before_apply/SHA256_preload.txt.  Idempotent only while nothing was written yet: refuses to overwrite an
existing backup with different bytes (a second run after the apply would otherwise destroy the pre-apply copy)."""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e25_followups/pass4/backup_before_apply"
FILES = """PL_breakdown.json
PL_breakdown_provenance.json
CSM_waterfall.json
CSM_waterfall_provenance.json
data/_gold/user_pl_cells.json
data/_gold/user_csm_cells.json
data/_gold/gold_overlay_ledger.json
data/_gold/pl_bridge_baseline.json
scripts/build_root_masters.py
tests/test_rule_coverage_manifest.py
tests/test_gold_overlay_survives_rebuild.py
tests/fixtures/master_tables_golden.json
tests/fixtures/builder_input_fingerprints.json
tests/fixtures/pl_breakdown_golden.json
data/_derived/qoq_warn.json
data/_derived/pl_oci_vs_bs_aoci_warn.json
data/_derived/pl_breakdown_coverage.json
data/_derived/pl_intentional_nulls.json
data/_derived/pl_oci_item32_provenance.json
data/dart/viz/csm_waterfall.json
data/dart/viz/csm_amort_schedule.json
data/dart/viz/insurance_pl_breakdown.json
data/dart/viz/bs_snapshot.json
data/dart/viz/sensitivity_heatmap.json
data/dart/viz/pl_breakdown_master.json
TODO_parser_ifrs17.md
docs/changelog_parser_ifrs17.md
inbox/parser/20261024T1000Z__orchestrator__KR0087-KR0032__2023.1Q-2024.4Q__complete_blocks_dongyang_nhfire.md
docs/todo_archive_parser_ifrs17.md""".split("\n")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head_sha(rel: str):
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


out, bad = [], []
for rel in FILES:
    src, dst = ROOT / rel, BK / rel
    if not src.exists():
        out.append(f"MISSING-SOURCE {rel}")
        bad.append(rel)
        continue
    h = sha(src)
    if dst.exists():
        if sha(dst) != h:
            out.append(f"EXISTS-DIFFERENT {rel} (backup {sha(dst)[:12]} vs source {h[:12]}): refusing to overwrite the pre-apply copy")
            bad.append(rel)
            continue
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    h2 = sha(dst)
    head = git_head_sha(rel)
    out.append(f"{'OK ' if h == h2 else 'BAD'} {h2}  {'HEAD-EQUAL' if head == h else ('HEAD-DIFFERS' if head else 'UNTRACKED')}  {rel}")
    if h != h2:
        bad.append(rel)
(BK / "SHA256_preload.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
print("PROBLEMS:", bad if bad else "none")
sys.exit(1 if bad else 0)
