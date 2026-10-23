# -*- coding: utf-8 -*-
"""Generate p3_apply.py from the audited pass2 applier (pass2/p2_apply.py <- e25_apply.py <- e23 ABL applier <- e21_apply.py).  Every substitution must match exactly once (asserted).
Changes versus p2_apply.py:
  - paths / plan file / notes for this batch (ticket 20261024T0600Z, neighbor stale cells sweep pass 3; PL only, no CSM file is written)
  - EV points at pass3/ (plan, drift snapshot, report, manifest all live there); backups under pass3/backup_before_apply
  - the merge note and the test-file comment are built from the plan counts at run time
  - build_gold documents the null_dangi additions / removals of this batch in a _doc_p3_20261024 key of the null_dangi block
Nothing else is changed: guards, simulation, provenance emitter, census/ledger checks and the revert path are the audited code."""
import re
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass2/p2_apply.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/p3_apply.py")
s = SRC.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f"anchor found {s.count(old)}x (need {count}): {old[:90]!r}"
    s = s.replace(old, new)


m = re.match(r'(#!/usr/bin/env python3\n# -\*- coding: utf-8 -\*-\n)"""(.*?)"""\n', s, re.S)
assert m
new_doc = '''"""Cell-level applier (parser/ifrs17, ticket 20261024T0600Z neighbor stale cells sweep pass 3, 2026-10-24).  Derived from the pass2 applier (pass2/p2_apply.py <- e25_apply.py <- e23 ABL applier <- e21_apply.py);
see make_apply_p3.py for the exact substitutions.  Input = p3_plan.json (apply_contract) produced by p01_build_plan.py and re-read independently by x01_verify_p3.py.

Writes (only these, each guarded + backed up under pass3/backup_before_apply/; the git HEAD copies are the second backup):
  data/_gold/user_pl_cells.json            +new set entries, in-place replaced set entry (stale static derived gold), +null_dangi / -null_dangi seam cells
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold (cell level: 값 and 값_당분기)
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one merge note key
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS (PL tuple)
  (gold_overlay_ledger.json only if a pinned cell vanishes: none planned)  No CSM file is written.

  --snapshot-drift   read-only: live masters vs a fresh build with the LIVE gold (all companies) -> pass3/drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline table -> p3_apply_report.txt)
  --out-dir DIR      write post-apply files under DIR (repo untouched)
  --apply            write the repo files
  --verify           read-only: a fresh build from the LIVE gold == the LIVE masters except the snapshot drift; planned cells equal
  --revert --apply   restore the backups (only while the live files still carry the post-apply hashes)
"""
'''
s = s[:m.start()] + m.group(1) + new_doc + s[m.end():]

rep('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass2"\n', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass3"\n')
rep('BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass2" / "backup_before_apply"', 'BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass3" / "backup_before_apply"')
rep('scratchpad/p2_tmp")', 'scratchpad/p3_tmp")')
rep('PLAN = json.loads((EV / "p2_plan.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "p3_plan.json").read_text(encoding="utf-8"))')
rep('manifest_path = EV / "apply_manifest_p2.json"', 'manifest_path = EV / "apply_manifest_p3.json"')
rep('(EV / "p2_apply_report.txt").write_text', '(EV / "p3_apply_report.txt").write_text')

# ---- merge note (built from the plan at run time)
a = s.index('MERGE_NOTE_KEY = "merge_note_20261024_pass2_neighbor_stale_cells"')
b = s.index("CSM_NOTE_KEY = None")
s = s[:a] + '''MERGE_NOTE_KEY = "merge_note_20261024_pass3_neighbor_stale_cells"
_NEW_N, _REP_N = len(C["gold_new"]), len(C["gold_replace"])
MERGE_NOTE = ("ticket 20261024T0600Z (neighbor stale cells sweep pass 3; ABL KR0070 2025.3Q-2026.2Q items 5/7/9/10/12 (current-period column of each quarter's own filing = latest), 동양 KR0087 2024.2Q reinsurance "
              "items 9/10/11/12 (FY2025 half-year prior-period analysis tables), NH농협손보 KR0032 2023.1Q items 20-24 + 2023.2Q items 22-24 / OCI 25-32 (FY2024 Q1 / half-year separate statement prior cumulative column)): "
              "PL cells refreshed to the latest comparative / latest print (separate basis) via data/_gold/user_pl_cells.json (%d new set cells + %d stale static derived-gold cell replaced in place; null_dangi +%d / -%d "
              "single-quarter cells; no ledger pins). Blocks that changed are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. "
              "Evidence data/_derived/remaining_20261022/e25_followups/pass3/" % (_NEW_N, _REP_N, len(C["null_dangi_add"]), len(C["null_dangi_remove"])))
''' + s[b:]

# ---- test-file comment
a = s.index('    comment = ("# 2026-10-24 ticket 20261024T0300Z')
b = s.index("    s = s[:m.start()] + comment")
s = s[:a] + '''    comment = ("# 2026-10-24 ticket 20261024T0600Z (parser/ifrs17 neighbor stale cells sweep pass 3: ABL 2025.3Q-2026.2Q items 5/9/10 and derived 7/12, 동양 2024.2Q reinsurance items 9-12, "
               "NH농협손보 2023.1Q/2Q income-statement tail items 20-24 and 2023.2Q OCI 25-32): "
               "CSM gold %d->%d cells, masked %d->%d; PL gold %d->%d cells, masked %d->%d (no new pins).\\n" % (census_old[0][0], census_new[0][0], census_old[0][1], census_new[0][1],
                                                                                                           census_old[1][0], census_new[1][0], census_old[1][1], census_new[1][1]))
''' + s[b:]

# ---- document the null_dangi changes of this batch
rep('''    for c, q, i in C["null_dangi_add"]:
        nd["cells"].append([c, q, i])
''', '''    for c, q, i in C["null_dangi_add"]:
        nd["cells"].append([c, q, i])
    if C["null_dangi_add"] or C["null_dangi_remove"]:
        assert "_doc_p3_20261024" not in nd
        nd["_doc_p3_20261024"] = ("2026-10-24 ticket 20261024T0600Z (parser/ifrs17, pass 3). REMOVED KR0070 2025.3Q item 5: with the corrected cumulative 7,271 (FY2025_Q3 current column) minus the 2025.2Q cumulative 4,605 the single quarter "
                                  "2,666 equals the 3-month column printed in the FY2025_Q3 report, so the builder derivation is right again. The item 7 blank of the same quarter is KEPT: the corrected derivation (-5,374.023) differs from the "
                                  "value implied by the printed 3-month cells (-5,372.023) by exactly 2.0 = the item 6 rounding noise between the FY2026_Q2 comparative and the FY2025_Q3 report (item 6 single -3,001 against printed -3,003). "
                                  "ADDED KR0087 2024.2Q and 2024.3Q item 11: the cumulatives of 2024.1Q (3,805), 2024.3Q (-479) and 2024.4Q (5,758) are the printed 재보험계약의 보험서비스결과 totals (= item 8), not the 예실차, so "
                                  "the difference of two cumulatives is meaningless (2024.2Q after this load: 14,273 - 3,805; 2024.3Q: -479 - 14,273). Blank beats wrong; the 2024.3Q detail is not printed in any filing.")
''')
DST.write_text(s, encoding="utf-8", newline="\n")
print("written", DST, len(s))
