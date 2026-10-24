# -*- coding: utf-8 -*-
"""Generate p4_apply.py from the audited pass3 applier (pass3/p3_apply.py <- pass2/p2_apply.py <- e25_apply.py <- e23 ABL applier <- e21_apply.py).  Every substitution must match exactly once (asserted).
Changes versus p3_apply.py:
  - paths / plan file / notes for this batch (ticket 20261024T1000Z, complete the blocks of 동양생명 reinsurance items 9-12 and NH농협손해보험 2023 statement; PL only, no CSM file is written)
  - EV points at pass4/ (plan, drift snapshot, report, manifest all live there); backups under pass4/backup_before_apply
  - gold entries may carry value null (blank cells, GOLD_SUPPRESSES precedent: KR0087 2025.3Q item 11): the planned-value equality check is None-safe
  - new optional contract key gold_note_append (note-only edit of an existing gold entry, value untouched; guarded by the exact old note)
  - the null_dangi additions / removals of this batch are documented in a _doc_p4_20261024 key of the null_dangi block
Nothing else is changed: guards, simulation, provenance emitter, census/ledger checks and the revert path are the audited code."""
import re
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/p3_apply.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass4/p4_apply.py")
s = SRC.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f"anchor found {s.count(old)}x (need {count}): {old[:90]!r}"
    s = s.replace(old, new)


m = re.match(r'(#!/usr/bin/env python3\n# -\*- coding: utf-8 -\*-\n)"""(.*?)"""\n', s, re.S)
assert m
new_doc = '''"""Cell-level applier (parser/ifrs17, ticket 20261024T1000Z complete the blocks of 동양생명 KR0087 reinsurance items 9-12 and NH농협손해보험 KR0032 2023 statement, 2026-10-24).  Derived from the pass3 applier
(pass3/p3_apply.py <- pass2/p2_apply.py <- e25_apply.py <- e23 ABL applier <- e21_apply.py); see make_apply_p4.py for the exact substitutions.  Input = p4_plan.json (apply_contract) produced by p01_build_plan.py.

Writes (only these, each guarded + backed up under pass4/backup_before_apply/; the git HEAD copies are the second backup):
  data/_gold/user_pl_cells.json            +new set entries (value may be null = blank cell), note-only appends on existing entries, +null_dangi / -null_dangi seam cells
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold (cell level: 값 and 값_당분기)
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one merge note key
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS (PL tuple)
  (gold_overlay_ledger.json only if a pinned cell vanishes: none planned)  No CSM file is written.

  --snapshot-drift   read-only: live masters vs a fresh build with the LIVE gold (all companies) -> pass4/drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline table -> p4_apply_report.txt)
  --out-dir DIR      write post-apply files under DIR (repo untouched)
  --apply            write the repo files
  --verify           read-only: a fresh build from the LIVE gold == the LIVE masters except the snapshot drift; planned cells equal
  --revert --apply   restore the backups (only while the live files still carry the post-apply hashes)
"""
'''
s = s[:m.start()] + m.group(1) + new_doc + s[m.end():]

rep('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass3"\n', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass4"\n')
rep('BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass3" / "backup_before_apply"', 'BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "pass4" / "backup_before_apply"')
rep('scratchpad/p3_tmp")', 'scratchpad/p4_tmp")')
rep('PLAN = json.loads((EV / "p3_plan.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "p4_plan.json").read_text(encoding="utf-8"))')
rep('manifest_path = EV / "apply_manifest_p3.json"', 'manifest_path = EV / "apply_manifest_p4.json"')
rep('(EV / "p3_apply_report.txt").write_text', '(EV / "p4_apply_report.txt").write_text')

# ---- merge note (built from the plan at run time)
a = s.index('MERGE_NOTE_KEY = "merge_note_20261024_pass3_neighbor_stale_cells"')
b = s.index("CSM_NOTE_KEY = None")
s = s[:a] + '''MERGE_NOTE_KEY = "merge_note_20261024_pass4_complete_blocks"
_NEW_N, _REP_N = len(C["gold_new"]), len(C["gold_replace"])
_BLANK_N = sum(1 for e in C["gold_new"] if e["value"] is None)
MERGE_NOTE = ("ticket 20261024T1000Z (complete the blocks; 동양 KR0087 2024.1Q/2024.3Q reinsurance items 9/10 (FY2025 1Q/3Q separate rollforward prior-period tables) and the two item 11 cells that held the "
              "보험서비스결과 total instead of the 예실차 (blanked); NH농협손보 KR0032 2023.2Q items 1/15/16/17/18/19/20/21 and 2023.1Q item 19 (FY2024 half-year / Q1 separate statement prior-period column)): "
              "PL cells refreshed to the latest comparative / latest print (separate basis) via data/_gold/user_pl_cells.json (%d new set cells, of which %d blanks (value null); %d note-only appends on existing pass-3 entries; "
              "null_dangi +%d / -%d single-quarter cells; no ledger pins). Blocks that changed are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. "
              "Evidence data/_derived/remaining_20261022/e25_followups/pass4/" % (_NEW_N, _BLANK_N, len(C.get("gold_note_append", [])), len(C["null_dangi_add"]), len(C["null_dangi_remove"])))
''' + s[b:]

# ---- test-file comment
a = s.index('    comment = ("# 2026-10-24 ticket 20261024T0600Z')
b = s.index("    s = s[:m.start()] + comment")
s = s[:a] + '''    comment = ("# 2026-10-24 ticket 20261024T1000Z (parser/ifrs17 complete the blocks: 동양 2024.1Q/2024.3Q reinsurance items 9-11, NH농협손보 2023.1Q/2Q statement items 1/15-21): "
               "CSM gold %d->%d cells, masked %d->%d; PL gold %d->%d cells, masked %d->%d (no new pins).\\n" % (census_old[0][0], census_new[0][0], census_old[0][1], census_new[0][1],
                                                                                                           census_old[1][0], census_new[1][0], census_old[1][1], census_new[1][1]))
''' + s[b:]

# ---- document the null_dangi changes of this batch
a = s.index('        assert "_doc_p3_20261024" not in nd')
b = s.index('Blank beats wrong; the 2024.3Q detail is not printed in any filing.")\n') + len('Blank beats wrong; the 2024.3Q detail is not printed in any filing.")\n')
s = s[:a] + '''        assert "_doc_p4_20261024" not in nd
        nd["_doc_p4_20261024"] = ("2026-10-24 ticket 20261024T1000Z (parser/ifrs17, pass 4). REMOVED KR0032 2023.2Q item 16: with the cumulative 40,748.545805 (FY2024_Q2 prior-period column; it replaces the 0.01-eok-rounded 6M value 41,900 "
                                  "of the 경영공시 summary PL) minus the 2023.1Q cumulative 20,951.967361 (e20) the single quarter 19,796.578444 equals the 3-month column printed in the FY2024_Q2 report to six decimals, so the builder "
                                  "derivation is right again (the e20 (c) blank is released). ADDED KR0087 2024.4Q items 9 and 10: the owner xlsx-fill cumulatives of 2024.4Q (-1,711 / +1,559; untouched) are on another sign/size than the new "
                                  "2024.3Q rollforward cumulatives (-3,079 / -1,180, FY2025_Q3 prior-period table), so the difference of the two cumulatives (+1,368 / +2,739) is not the fourth quarter; those 4Q single quarters stay blank, as they "
                                  "were before this load (the 3Q cumulative was blank). Blank beats wrong; re-derive once the owner settles the 4Q cumulatives / the series sign convention.")
''' + s[b:]

# ---- gold_note_append: apply in build_gold (note-only edit, value untouched)
rep('''        ent["값"], ent["was"], ent["note"] = e["value"], e["was"], e["note"]
    for e in C["gold_new"]:
''', '''        ent["값"], ent["was"], ent["note"] = e["value"], e["was"], e["note"]
    for e in C.get("gold_note_append", []):
        ent = g["set"][idx[(e["code"], e["item"], e["quarter"])]]
        assert ent["note"] == e["old_note"] and ent["값"] == e["value"], (e["code"], e["item"], e["quarter"])
        ent["note"] = ent["note"] + e["append"]
    for e in C["gold_new"]:
''')
# ---- guard for gold_note_append
rep('''    for c, q, i in C["null_dangi_add"]:
        if (c, q, i) in nd or (c, q, i) in sd:
            bad.append(("null_dangi_add: dangi list already has", (c, q, i)))
''', '''    for e in C.get("gold_note_append", []):
        k = (e["code"], e["item"], e["quarter"])
        ge = gold_by.get(k)
        if ge is None or ge["note"] != e["old_note"] or ge["값"] != e["value"]:
            bad.append(("gold_note_append: entry missing / note or value moved since the plan", k))
    for c, q, i in C["null_dangi_add"]:
        if (c, q, i) in nd or (c, q, i) in sd:
            bad.append(("null_dangi_add: dangi list already has", (c, q, i)))
''')
# ---- None-safe equality of the planned value (blank cells)
rep('''        if abs(new_by[k]["값"] - e["value"]) > 1e-9:
            errs.append(f"PL new build value {k}: {new_by[k]['값']} != plan {e['value']}")''', '''        if (new_by[k]["값"] is None) != (e["value"] is None) or (e["value"] is not None and abs(new_by[k]["값"] - e["value"]) > 1e-9):
            errs.append(f"PL new build value {k}: {new_by[k]['값']} != plan {e['value']}")''')
DST.write_text(s, encoding="utf-8", newline="\n")
print("written", DST, len(s))
