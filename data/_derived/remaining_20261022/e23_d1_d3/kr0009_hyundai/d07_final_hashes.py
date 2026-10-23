# -*- coding: utf-8 -*-
"""read-only: sha256 of every repo file this load changed (final state) next to its pre-load sha256 (backup) and the apply manifest's after hash for the 7 applier files"""
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
BK = EV / "backup_before_apply/kr0009_hyundai"
man = json.loads((EV / "kr0009_hyundai/apply_manifest_e23_hd.json").read_text(encoding="utf-8"))
FILES = ["PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
         "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
         "data/_derived/qoq_warn.json", "data/_derived/pl_oci_vs_bs_aoci_warn.json"]
UNCHANGED = ["data/_gold/gold_overlay_ledger.json", "tests/fixtures/pl_breakdown_golden.json", "tests/fixtures/viz_ifrs17_panels_golden.json", "tests/fixtures/viz_csm_waterfall_golden.json",
             "NB_CSM_multiple.json", "data/dart/viz/pl_breakdown_master.json", "insurequant_master_tables.xlsx"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


out = []
for rel in FILES:
    now, pre = sha(ROOT / rel), sha(BK / rel)
    mark = ""
    if rel in man["after_sha256"]:
        mark = "== apply manifest after_sha256" if man["after_sha256"][rel] == now else "!= apply manifest after_sha256 (changed after the apply)"
    out.append(f"CHANGED   {rel}\n          pre-load {pre}\n          final    {now}  {mark}")
for rel in UNCHANGED:
    p = BK / rel
    now = sha(ROOT / rel)
    out.append(f"UNCHANGED {rel}: {'same as pre-load backup' if (p.exists() and sha(p) == now) else ('not in backup; sha ' + now[:16])}")
(EV / "kr0009_hyundai/final_state_sha256.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
