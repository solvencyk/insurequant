# -*- coding: utf-8 -*-
"""pass3 x03 (read-only): every file backed up in backup_before_apply/ is compared with the live file; the expected-changed set is listed, everything else must be byte-identical."""
import hashlib
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e25_followups/pass3/backup_before_apply"
EXPECT_CHANGED = {"PL_breakdown.json", "PL_breakdown_provenance.json", "data/_gold/user_pl_cells.json", "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json",
                  "TODO_parser_ifrs17.md", "docs/changelog_parser_ifrs17.md", "docs/todo_archive_parser_ifrs17.md",
                  "inbox/parser/20261024T0600Z__orchestrator__MULTI__2023.2Q-2026.2Q__neighbor_stale_cells_pass3_abl_dongyang_nhfire.md"}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bad, same, changed = [], [], []
for p in sorted(BK.rglob("*")):
    if not p.is_file() or p.name == "SHA256_preload.txt":
        continue
    rel = p.relative_to(BK).as_posix()
    live = ROOT / rel
    eq = live.exists() and sha(live) == sha(p)
    if rel in EXPECT_CHANGED:
        changed.append((rel, not eq))
        if eq:
            bad.append(f"expected changed but identical: {rel}")
    else:
        same.append(rel)
        if not eq:
            bad.append(f"UNEXPECTED CHANGE: {rel}")
print("byte-identical (must be unchanged):", len(same))
for r in same:
    print("   =", r)
print("changed as expected:", [(r, c) for r, c in changed])
print("PROBLEMS:", bad if bad else "none")
