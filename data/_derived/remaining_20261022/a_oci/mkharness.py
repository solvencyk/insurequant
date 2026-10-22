import re
from pathlib import Path
p = Path("apply_kr0073_oci.py")
s = p.read_text(encoding="utf-8")
def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:60], s.count(old))
    s = s.replace(old, new)

sub('''"""Cell-level applier (parser/ifrs17, ticket 20261021T1310Z follow-up, coordinator approval 2026-10-22):
KR0073 (Kyobo Life) PL_breakdown 2023.1Q-2024.2Q refreshed to the latest-comparative (restated) separate-basis columns.
''', '''"""Cell-level applier (parser/ifrs17, ticket 20261021T1556Z, owner instruction 2026-10-22):
KR0073 (Kyobo Life) PL_breakdown OCI items of 2024.4Q / 2025.1Q / 2025.2Q (13 cells) refreshed to the latest-comparative (restated) separate-basis cumulative columns.
Adapted from data/_derived/kyobo_pl_restate_dryrun_20261021/apply_kr0073_pl_refresh.py (same procedure; evidence dir = this folder; backups live OUTSIDE the repo, in the scratchpad).
''')
sub('EV = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"',
    'OLD_EV = ROOT / "data" / "_derived" / "kyobo_pl_restate_dryrun_20261021"\nEV = ROOT / "data" / "_derived" / "remaining_20261022" / "a_oci"\nBACKUP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/a_oci_backup")')
sub('for p in (str(ROOT / "scripts"), str(ROOT), str(EV)):', 'for p in (str(ROOT / "scripts"), str(ROOT), str(OLD_EV), str(EV)):')
sub('QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]', 'QS = ["2024.4Q", "2025.1Q", "2025.2Q"]')
sub('''LATER = {"2023.1Q": ("FY2024_Q1", "20240516001553"), "2023.2Q": ("FY2024_Q2", "20240814004365"), "2023.3Q": ("FY2024_Q3", "20241114003039"),
         "2023.4Q": ("FY2024_Q4", "20250331004015"), "2024.1Q": ("FY2025_Q1", "20250515002967"), "2024.2Q": ("FY2025_Q2", "20250814004112")}''',
    '''LATER = {"2024.4Q": ("FY2025_Q4 annual", "20260331004015"), "2025.1Q": ("FY2026_Q1", "20260813001077"), "2025.2Q": ("FY2026_Q2", "20260814004024")}''')
sub('EXPECT = {"gold_added": 122, "val_changed": 122, "dangi_changed": 152, "census_old": (360, 29), "census_new": (482, 29), "prov_blocks": 12}',
    'EXPECT = {"gold_added": 13, "val_changed": 13, "dangi_changed": None, "census_old": (482, 29), "census_new": (495, 29), "prov_blocks": 6}')
# merge note
i = s.index("MERGE_NOTE = (")
j = s.index("SUBS = [")
s = s[:i] + '''MERGE_NOTE = ("KR0073 PL OCI items (25/26/29/31/32) of 2024.4Q, 2025.1Q, 2025.2Q refreshed to the latest-comparative (restated) separate-basis cumulative columns via data/_gold/user_pl_cells.json (+13 cells). "
              "The 6 blocks of those quarters are the output of scripts/emit_pl_provenance.py for the post-apply masters. Evidence data/_derived/remaining_20261022/a_oci/")
''' + s[j:]
# note text
i = s.index("        fy, rc = LATER[c[\"quarter\"]]")
j = s.index("        g[\"set\"].append(")
s = s[:i] + '''        fy, rc = LATER[c["quarter"]]
        note = NOTES[(c["quarter"], c["item"])]
''' + s[j:]
# plan path / cand checks removal
sub('''    # what is applied == what was gated in the dry run
    cand_master = load_json(EV / "sim" / "cand_pl.json")
    if cand_master != new_rows:
        diff = [rkey(a) for a, b in zip(cand_master, new_rows) if a != b]
        errs.append(f"post-apply master differs from the gated candidate sim/cand_pl.json in {len(diff)} rows (e.g. {diff[:3]})")
    if load_json(EV / "sim" / "gold_pl_cand.json") != new_gold:
        errs.append("post-apply gold differs from the gated candidate sim/gold_pl_cand.json")

''', '')
sub('''    if load_json(EV / "sim" / "prov_pl_cand_emitter.json") != new_prov:
        errs.append("post-apply provenance differs from the gated candidate sim/prov_pl_cand_emitter.json")
''', '')
sub('if len(val_changed) != EXPECT["val_changed"] or len(dangi_changed) != EXPECT["dangi_changed"]:\n        errs.append(f"counts: 값 {len(val_changed)} (exp {EXPECT[\'val_changed\']}), 당분기 {len(dangi_changed)} (exp {EXPECT[\'dangi_changed\']})")',
    'if len(val_changed) != EXPECT["val_changed"]:\n        errs.append(f"counts: 값 {len(val_changed)} (exp {EXPECT[\'val_changed\']})")')
# comment line in test
sub('comment = ("# 2026-10-22 ticket 20261021T1310Z (parser/ifrs17, KR0073 PL refresh to the latest comparative): PL gold %d->%d cells, masked %d->%d (no new pins).\\n"',
    'comment = ("# 2026-10-22 ticket 20261021T1556Z (parser/ifrs17, KR0073 OCI items 2024.4Q-2025.2Q refreshed to the latest comparative): PL gold %d->%d cells, masked %d->%d (no new pins).\\n"')
# backup dir
sub('backup = EV / "backup_before_apply_PL"', 'backup = BACKUP')
sub('manifest_path = EV / "apply_manifest_PL.json"', 'manifest_path = EV / "apply_manifest_oci.json"')
# plan path
sub('plan = load_json(EV / "pl_plan.json")["plan"]', 'plan = load_json(EV / "pl_plan.json")["plan"]')
# tmp dirs
sub('tmpdir = EV / "tmp_apply"', 'tmpdir = BACKUP / "tmp_apply"')
sub('d = EV / "tmp_emit"', 'd = BACKUP / "tmp_emit"')
sub('d.mkdir(exist_ok=True)', 'd.mkdir(parents=True, exist_ok=True)')
sub('tmpdir.mkdir(exist_ok=True)', 'tmpdir.mkdir(parents=True, exist_ok=True)')
sub('snap_path = EV / "pl_drift_before.json"', 'snap_path = EV / "pl_drift_before.json"')
# emitter sandbox copy lives in the old evidence folder
sub('(EV / "emit_pl_provenance_sandbox_copy.py").read_text(encoding="utf-8")', '(OLD_EV / "emit_pl_provenance_sandbox_copy.py").read_text(encoding="utf-8")')
sub('[PY, str(EV / "emit_pl_provenance_sandbox_copy.py")]', '[PY, str(OLD_EV / "emit_pl_provenance_sandbox_copy.py")]')
sub('ak = _load(CSM_EV / "apply_kr0073_fix.py", "ak_helpers")', 'ak = _load(CSM_EV / "apply_kr0073_fix.py", "ak_helpers")')
# NOTES import
sub('def rkey(r):', 'NOTES = json.loads((EV / "gold_notes.json").read_text(encoding="utf-8"))\nNOTES = {(k.split("|")[0], int(k.split("|")[1])): v for k, v in NOTES.items()}\n\n\ndef rkey(r):')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
