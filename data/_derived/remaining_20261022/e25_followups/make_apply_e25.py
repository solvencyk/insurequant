# -*- coding: utf-8 -*-
"""Generate e25_apply.py from the audited ABL applier (e23_d1_d3/kr0070_abl/e23_apply.py).  Every substitution must match exactly once (asserted).
Changes versus the ABL applier:
  - constants / plan path / notes for this batch (four tickets, PL only: no CSM file is written)
  - drift_fix: cells whose LIVE value differs from a fresh build_pl() with the live gold because they were hand-loaded (not gold) are set to the fresh-build value
    (KB손해보험 item 16 2024.4Q / 2025.2Q: 60,900 / 33,300 -> blank); guarded: live == plan value, fresh build == plan value, not a gold cell
  - CSM parts: build_cprov returns the live sidecar unchanged and outputs() carries no CSM file (the CSM simulation stays as a no-change sanity check)
  - two more identity lines in the report: 3 = 4+5+6+7 and 8 = 9+10+11+12
  - verify(): the drift-fix cells must equal a fresh build"""
import re
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/e23_apply.py")
DST = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/e25_apply.py")
s = SRC.read_text(encoding="utf-8")


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f"anchor found {s.count(old)}x (need {count}): {old[:80]!r}"
    s = s.replace(old, new)


# ---- docstring
m = re.match(r'(#!/usr/bin/env python3\n# -\*- coding: utf-8 -\*-\n)"""(.*?)"""\n', s, re.S)
assert m
new_doc = '''"""Cell-level applier (parser/ifrs17, tickets 20261023T1130Z KB라이프 / 20261023T1210Z ABL / 20261023T0600Z 농협생명 / 20261024T0100Z KB손해보험, 2026-10-24).  Derived from the ABL applier
(kr0070_abl/e23_apply.py <- Lotte variant <- e21_apply.py, audited in the READY-25 / D1-D3 loads); see make_apply_e25.py for the exact substitutions.
Input = e25_plan.json (apply_contract) produced by p01_build_plan.py and re-read independently by x01_verify_e25.py.

Writes (only these, each guarded + backed up under backup_before_apply/; the git HEAD copies are the second backup):
  data/_gold/user_pl_cells.json            +new set entries, 1 replaced set entry (ABL 2023.1Q item 7)
  PL_breakdown.json                        ONLY the cells where a REAL build_pl() run (temp copy) with the new gold differs from the same run with the live gold (cell level: 값 and 값_당분기)
                                           + the drift_fix cells (hand-loaded live value -> the value a fresh build writes)
  PL_breakdown_provenance.json             blocks whose emitter output changes (sandbox copy of scripts/emit_pl_provenance.py; never imported) + one merge note key
  tests/test_rule_coverage_manifest.py     GOLD_OVERLAY_CENSUS (PL tuple)
  (gold_overlay_ledger.json only if a pinned cell vanishes: none planned)  No CSM file is written.

  --snapshot-drift   read-only: live masters vs a fresh build with the LIVE gold (all companies) -> drift_before.json (run BEFORE --apply)
  --check            read-only plan + post-condition checks (+ identity residuals, headline table -> e25_apply_report.txt)
  --out-dir DIR      write post-apply files under DIR (repo untouched)
  --apply            write the repo files
  --verify           read-only: a fresh build from the LIVE gold == the LIVE masters except the snapshot drift; planned cells equal
  --revert --apply   restore the backups (only while the live files still carry the post-apply hashes)
"""
'''
s = s[:m.start()] + m.group(1) + new_doc + s[m.end():]

# ---- constants
rep('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "kr0070_abl"', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups"')
rep('BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "backup_before_apply" / "kr0070_abl"', 'BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e25_followups" / "backup_before_apply"')
rep('scratchpad/e23_kr0070_tmp")', 'scratchpad/e25_tmp")')
rep('PLAN = json.loads((EV / "e23_plan_abl_final.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "e25_plan.json").read_text(encoding="utf-8"))')
rep('STALE_NONE_OK = {("KR0070", 16, "2023.4Q")}', 'STALE_NONE_OK = set()')

# ---- notes
a = s.index('MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0070_abl"')
b = s.index("SUBS = [")
s = s[:a] + '''MERGE_NOTE_KEY = "merge_note_20261024_e25_followups"
MERGE_NOTE = ("tickets 20261023T1130Z (KB라이프 KR0099 2023.1Q items 9/11/12), 20261023T1210Z (ABL KR0070 FY2023 items 5/6/7/9/10), 20261023T0600Z (농협생명 KR0104 2024.1Q/2Q items 17/18/20/21), "
              "20261024T0100Z (KB손해보험 KR0010 item 16 2024.4Q/2025.2Q hand-loaded 경영공시 요약 PL values removed): PL cells refreshed to the latest comparative (separate basis, prior-period cumulative column of the "
              "FY2024 Q1/H1/Q3/annual reports of KB라이프 / ABL and the FY2025 Q1/H1 reports of 농협생명) via data/_gold/user_pl_cells.json (29 new set cells + 1 owner-gold cell replaced in place: ABL 2023.1Q item 7; "
              "no single-quarter pins, no ledger pins). Blocks that changed are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. "
              "Evidence data/_derived/remaining_20261022/e25_followups/")
CSM_NOTE_KEY = None
CSM_NOTE = None
''' + s[b:]

# ---- guard: drift_fix
rep('''    if bad:
        raise SystemExit(f"ABORT: live files moved since the plan was made (concurrent session?) or overlap: {bad[:6]} ... ({len(bad)})")''',
    '''    for e in C.get("drift_fix", []):
        k = (e["code"], e["item"], e["quarter"])
        r = cur.get(k)
        if r is None or not same(r.get("값"), e["live_value"]):
            bad.append(("drift_fix: live value != plan", k, e["live_value"], None if r is None else r.get("값")))
        if k in gold_by:
            bad.append(("drift_fix: the cell has a gold entry", k))
    if bad:
        raise SystemExit(f"ABORT: live files moved since the plan was made (concurrent session?) or overlap: {bad[:6]} ... ({len(bad)})")''')

# ---- build_cprov: no CSM change in this batch
rep('''def build_cprov(live_cprov, new_cgold):
    new = copy.deepcopy(live_cprov)''', '''def build_cprov(live_cprov, new_cgold):
    if not (C["csm_gold_new"] or C["csm_gold_replace"] or C["csm_gold_remove"]):
        return copy.deepcopy(live_cprov), [], []          # no CSM cell in this batch: the CSM sidecar stays byte-identical
    new = copy.deepcopy(live_cprov)''')

# ---- plan_all: drift_fix applied after build_master
rep('''    new_rows, delta, val_changed, dangi_changed, pre_drift_on_delta = build_master(live["PL"].obj, base_rows, new_sim)
    errs = []''', '''    new_rows, delta, val_changed, dangi_changed, pre_drift_on_delta = build_master(live["PL"].obj, base_rows, new_sim)
    errs = []
    # drift_fix: hand-loaded live cells (not gold) -> the value a fresh build writes; guarded against the fresh build itself
    fix_keys = {(e["code"], e["item"], e["quarter"]): e for e in C.get("drift_fix", [])}
    base_by_fix = {rkey(r): r for r in base_rows}
    for k, e in fix_keys.items():
        if k in {(x["code"], x["item"], x["quarter"]) for x in C["gold_new"] + C["gold_replace"]}:
            errs.append(f"drift_fix {k} is also a planned gold cell")
        if not same(base_by_fix[k]["값"], e["fresh_value"]):
            errs.append(f"drift_fix {k}: fresh build value {base_by_fix[k]['값']} != plan {e['fresh_value']}")
        if base_by_fix[k].get("값_당분기") != next(r for r in live["PL"].obj if rkey(r) == k).get("값_당분기"):
            errs.append(f"drift_fix {k}: fresh 값_당분기 != live 값_당분기")
        if k in delta:
            errs.append(f"drift_fix {k} is inside the gold delta")
    if fix_keys:
        new_rows = [dict(r, **{"값": base_by_fix[rkey(r)]["값"], "값_당분기": base_by_fix[rkey(r)].get("값_당분기")}) if rkey(r) in fix_keys else r for r in new_rows]''')

# ---- verify(): drift_fix cells equal a fresh build
rep('''    ok1b = all((by[k]["값_당분기"] is None) if v is None else (by[k]["값_당분기"] is not None and abs(by[k]["값_당분기"] - v) <= 1e-6) for k, v in exp.items())''',
    '''    ok1b = all((by[k]["값_당분기"] is None) if v is None else (by[k]["값_당분기"] is not None and abs(by[k]["값_당분기"] - v) <= 1e-6) for k, v in exp.items())
    fixk = [(e["code"], e["item"], e["quarter"]) for e in C.get("drift_fix", [])]
    ok1b = ok1b and all(by[k]["값"] == bs[k]["값"] and by[k]["값_당분기"] == bs[k]["값_당분기"] for k in fixk)
    print(f"verify PL: drift-fix cells {fixk} equal a fresh build -> {'OK' if all(by[k]['값'] == bs[k]['값'] for k in fixk) else 'FAIL'}")''')

# ---- outputs(): no CSM file
rep('''    outs = {F["GOLD"]: ak.JsonFile._dump(P["new_gold"], *L["GOLD"].fmt), F["PL"]: ak.JsonFile._dump(P["new_rows"], *L["PL"].fmt),
            F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), F["CGOLD"]: ak.JsonFile._dump(P["new_cgold"], *L["CGOLD"].fmt),
            F["CSM"]: ak.JsonFile._dump(P["new_csm"], *L["CSM"].fmt), F["CPROV"]: ak.JsonFile._dump(P["new_cprov"], *L["CPROV"].fmt), TEST_REL: P["new_test"]}''',
    '''    outs = {F["GOLD"]: ak.JsonFile._dump(P["new_gold"], *L["GOLD"].fmt), F["PL"]: ak.JsonFile._dump(P["new_rows"], *L["PL"].fmt),
            F["PROV"]: ak.JsonFile._dump(P["new_prov"], *L["PROV"].fmt), TEST_REL: P["new_test"]}''')

# ---- test file comment (census declaration)
a = s.index('    comment = ("# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 에이비엘생명보험 KR0070')
b = s.index("    s = s[:m.start()] + comment + m.group(1)")
s = s[:a] + '''    comment = ("# 2026-10-24 tickets 20261023T1130Z / 20261023T1210Z / 20261023T0600Z / 20261024T0100Z (parser/ifrs17 follow-ups: KB라이프 2023.1Q items 9/11/12, ABL FY2023 items 5/6/7/9/10, 농협생명 2024.1Q/2Q items 17/18/20/21 refreshed to the latest comparative; "
               "1 PL owner-gold cell replaced in place (ABL 2023.1Q item 7); KB손해보험 item 16 hand-loaded values removed): "
               "CSM gold %d->%d cells, masked %d->%d; PL gold %d->%d cells, masked %d->%d (no new pins).\\n" % (census_old[0][0], census_new[0][0], census_old[0][1], census_new[0][1],
                                                                                                          census_old[1][0], census_new[1][0], census_old[1][1], census_new[1][1]))
''' + s[b:]

# ---- tax22 branch: this batch must not move the TAX22 set (the Lotte/ABL comment anchors of the old applier are not carried over)
a = s.index("    if tax_off_new != tax_off_old:")
b = s.index("    out = s.replace(\"\\n\", \"\\r\\n\") if crlf else s")
s = s[:a] + '''    if tax_off_new != tax_off_old:
        raise SystemExit("ABORT: the TAX22 latest-comparative-only bucket set moved in this batch (not expected: items 22/23/24 are untouched); regenerate _TAX22_LATEST_COMPARATIVE_ONLY by hand")
''' + s[b:]

# ---- identity lines
rep('''    ("17-(18+19)", lambda v: _d(v, 17, (18, 19))),
]''', '''    ("17-(18+19)", lambda v: _d(v, 17, (18, 19))),
    ("3-(4+5+6+7)", lambda v: _d(v, 3, (4, 5, 6, 7))),
    ("8-(9+10+11+12)", lambda v: _d(v, 8, (9, 10, 11, 12))),
]''')

# ---- manifest name + revert path
rep('manifest_path = EV / "apply_manifest_e23_abl.json"', 'manifest_path = EV / "apply_manifest_e25.json"')
rep('(EV / "e23_apply_report.txt")', '(EV / "e25_apply_report.txt")')
# header comment inside report() uses P["census"]; nothing to change there

DST.write_text(s, encoding="utf-8", newline="\n")
print("wrote", DST, len(s), "bytes")
