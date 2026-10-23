# -*- coding: utf-8 -*-
"""Generate p2_apply.py from the audited e25 applier (e25_followups/e25_apply.py <- ABL e23 applier <- Lotte variant <- e21_apply.py).  Every substitution must match exactly once (asserted).
Changes versus e25_apply.py:
  - paths / plan file / notes for this batch (ticket 20261024T0300Z, neighbor stale cells sweep pass 2; PL only, no CSM file is written)
  - EV points at pass2/ (plan, drift snapshot, report, manifest all live there); backups under pass2/backup_before_apply
  - the merge note and the test-file comment are built from the plan counts at run time
Nothing else is changed: guards, simulation, provenance emitter, census/ledger checks and the revert path are the audited code."""
import re
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/e25_apply.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2/p2_apply.py")
s = SRC.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f"anchor found {s.count(old)}x (need {count}): {old[:90]!r}"
    s = s.replace(old, new)


m = re.match(r'(#!/usr/bin/env python3\n# -\*- coding: utf-8 -\*-\n)"""(.*?)"""\n', s, re.S)
assert m
new_doc = '''"""Cell-level applier (parser/ifrs17, ticket 20261024T0300Z neighbor stale cells sweep pass 2, 2026-10-24).  Derived from the e25 applier (e25_followups/e25_apply.py <- e23 ABL applier <- e21_apply.py);
see make_apply_p2.py for the exact substitutions.  Input = p2_plan.json (apply_contract) produced by p01_build_plan.py and re-read independently by x01_verify_p2.py.

Writes (only these, each guarded + backed up under pass2/backup_before_apply/; the git HEAD copies are the second backup):
  data/_gold/user_pl_cells.json            +new set entries, in-place replaced set entries (stale static derived gold), +null_dangi / +set_dangi seam cells
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold (cell level: 값 and 값_당분기)
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one merge note key
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS (PL tuple)
  (gold_overlay_ledger.json only if a pinned cell vanishes: none planned)  No CSM file is written.

  --snapshot-drift   read-only: live masters vs a fresh build with the LIVE gold (all companies) -> pass2/drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline table -> p2_apply_report.txt)
  --out-dir DIR      write post-apply files under DIR (repo untouched)
  --apply            write the repo files
  --verify           read-only: a fresh build from the LIVE gold == the LIVE masters except the snapshot drift; planned cells equal
  --revert --apply   restore the backups (only while the live files still carry the post-apply hashes)
"""
'''
s = s[:m.start()] + m.group(1) + new_doc + s[m.end():]

rep('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups"\n', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass2"\n')
rep('BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "backup_before_apply"', 'BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass2" / "backup_before_apply"')
rep('scratchpad/e25_tmp")', 'scratchpad/p2_tmp")')
rep('PLAN = json.loads((EV / "e25_plan.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "p2_plan.json").read_text(encoding="utf-8"))')
rep('manifest_path = EV / "apply_manifest_e25.json"', 'manifest_path = EV / "apply_manifest_p2.json"')
rep('(EV / "e25_apply_report.txt").write_text', '(EV / "p2_apply_report.txt").write_text')

# ---- merge note (built from the plan at run time)
a = s.index('MERGE_NOTE_KEY = "merge_note_20261024_e25_followups"')
b = s.index("CSM_NOTE_KEY = None")
s = s[:a] + '''MERGE_NOTE_KEY = "merge_note_20261024_pass2_neighbor_stale_cells"
_NEW_N, _REP_N = len(C["gold_new"]), len(C["gold_replace"])
MERGE_NOTE = ("ticket 20261024T0300Z (neighbor stale cells sweep pass 2; ABL KR0070 2023.1Q-2025.2Q items 5/7/9/10/11/12, 동양 KR0087 2024.2Q/3Q items 5/6/7, 현대해상 KR0009 2023.1Q/2Q items 5/9/10, "
              "한화생명 KR0068 2023.1Q-4Q items 5/6/7/9/10/11/12, NH농협손보 KR0032 2023.1Q + DB생명 KR0082 2023.1Q/2Q OCI items 25-32): PL cells refreshed to the latest comparative (separate basis, prior-period "
              "cumulative column of the next fiscal year's same-quarter filing) via data/_gold/user_pl_cells.json (%d new set cells + %d stale static derived-gold cells replaced in place; null_dangi +%d, set_dangi +%d "
              "single-quarter seam cells; no ledger pins). Blocks that changed are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. "
              "Evidence data/_derived/remaining_20261022/e25_followups/pass2/" % (_NEW_N, _REP_N, len(C["null_dangi_add"]), len(C["set_dangi_add"])))
''' + s[b:]

# ---- test-file comment
a = s.index('    comment = ("# 2026-10-24 tickets 20261023T1130Z')
b = s.index("    s = s[:m.start()] + comment")
s = s[:a] + '''    comment = ("# 2026-10-24 ticket 20261024T0300Z (parser/ifrs17 neighbor stale cells sweep pass 2: ABL / 동양 / 현대해상 / 한화생명 note items refreshed to the latest comparative, stale static derived gold (items 7 / 12) recomputed in place, "
               "NH농협손보 + DB생명 OCI blanks filled): "
               "CSM gold %d->%d cells, masked %d->%d; PL gold %d->%d cells, masked %d->%d (no new pins).\\n" % (census_old[0][0], census_new[0][0], census_old[0][1], census_new[0][1],
                                                                                                           census_old[1][0], census_new[1][0], census_old[1][1], census_new[1][1]))
''' + s[b:]
DST.write_text(s, encoding="utf-8", newline="\n")
print("written", DST, len(s))
