# -*- coding: utf-8 -*-
"""k09: sha256 of the 19 files in the live tree vs the pre-load backup copies (read-only).

Usage: python k09_hash_vs_backup.py [LABEL]      exit code 0 = all 19 identical, 1 = at least one differs.
"""
import hashlib
import sys
import time

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
BK = REPO + "/data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2"
OUT = REPO + "/data/_derived/remaining_20261022/e23_d1_d3/kdb_restore/k09_hash_vs_backup.log"
LABEL = sys.argv[1] if len(sys.argv) > 1 else ""

FILES = [
    "PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json",
    "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json",
    "data/_gold/user_csm_cells.json", "data/_gold/gold_overlay_ledger.json",
    "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json",
    "tests/fixtures/builder_input_fingerprints.json", "tests/fixtures/pl_breakdown_golden.json",
    "tests/fixtures/viz_ifrs17_panels_golden.json", "tests/fixtures/viz_csm_waterfall_golden.json",
    "data/_derived/pl_oci_vs_bs_aoci_warn.json", "data/_derived/qoq_warn.json",
    "data/dart/viz/csm_continuity_validation.json", "NB_CSM_multiple.json",
    "data/dart/viz/pl_breakdown_master.json", "scripts/validate_master_tables.py",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    lines = ["%s  k09 %s" % (time.strftime("%H:%M:%S"), LABEL)]
    bad = 0
    for rel in FILES:
        a, b = sha(REPO + "/" + rel), sha(BK + "/" + rel)
        ok = a == b
        bad += 0 if ok else 1
        lines.append("%s  %s  live %s  backup %s" % ("same" if ok else "DIFF", rel, a[:16], b[:16]))
    lines.append("RESULT %s: %d of %d files differ from the backup" % (LABEL, bad, len(FILES)))
    text = "\n".join(lines) + "\n"
    with open(OUT, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
