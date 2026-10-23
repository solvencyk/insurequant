# -*- coding: utf-8 -*-
"""Derive this folder's applier / checkers for the KDB (KR0072) LOAD 2 from the audited copies of the first (held) attempt in ../kr0072_kdb/ by asserted substitutions (each must hit exactly once).
State of the tree is now the state after the Hyundai (KR0009) load of this chain + the validation cleanup (item 23 BLIND declaration, WFY exemption of Lotte FY2023).  The audited logic (guards, real
build_pl()/build_csm() sandbox deltas, sandbox emitter, ledger/census/test updates, verify, revert) is unchanged; the changes are paths, the Hyundai predecessor state and the TAX22 comment anchor.
Read-only on every master / gold / provenance / test / doc."""
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "kr0072_kdb"
SCR = "C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad"


def patch(name, subs, dst_name=None):
    s = (OLD / name).read_text(encoding="utf-8")
    for a, b in subs:
        assert s.count(a) == 1, (name, s.count(a), a[:120])
        s = s.replace(a, b)
    (HERE / (dst_name or name)).write_text(s, encoding="utf-8", newline="\n")
    print("wrote", dst_name or name, len(s))


# ------------------------------------------------------------------------------------------------ the applier
tax_old = '''        old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: 에이비엘생명보험 FY2023 2023.1Q-2023.4Q .*\\n", s, re.M)
        if old_c is None:
            raise SystemExit("ABORT: the TAX22 comment of the ABL load (ticket 20261023T0900Z) was not found")'''
tax_new = '''        old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: 현대해상 FY2023 2023.1Q-2023.4Q .*\\n", s, re.M)
        if old_c is None:
            raise SystemExit("ABORT: the TAX22 comment of the Hyundai load (ticket 20261023T0900Z) was not found")'''
patch("e23_apply.py", [
    ('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "kr0072_kdb"\n', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "kr0072_kdb_load2"\n'),
    ('"backup_before_apply" / "kr0072_kdb"\n', '"backup_before_apply" / "kr0072_kdb_load2"\n'),
    ('scratchpad/e23_kr0072_tmp")', 'scratchpad/e23_kr0072_load2_tmp")'),
    ('(sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/")', '(sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2/")'),
    ('cleared on the 2023.4Q block). Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/")', 'cleared on the 2023.4Q block). Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2/")'),
    (tax_old, tax_new),
])

# ------------------------------------------------------------------------------------------------ checkers
patch("kr0072_diff_vs_backup.py", [
    ('BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb"\n', 'BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2"\n'),
    ('ABL_MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/apply_manifest_e23_abl.json").read_text(encoding="utf-8"))\n',
     'ABL_MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0009_hyundai/apply_manifest_e23_hd.json").read_text(encoding="utf-8"))   # the HYUNDAI manifest: the state right before this load\n'),
    ('for rel, h in ABL_MAN["after_sha256"].items():\n    chk(f"backup {rel} == ABL manifest after_sha256 (= state right before this load)"',
     'for rel, h in ABL_MAN["after_sha256"].items():\n    if rel.startswith("tests/"):\n        continue   # the test file was edited afterwards by the validation cleanup (checked against its post copy in a01_precheck.py)\n    chk(f"backup {rel} == Hyundai manifest after_sha256 (= state right before this load)"'),
    ("(KR0099, KR0003, KR0070 and all others untouched)", "(KR0099, KR0003, KR0070, KR0009 and all others untouched)"),
    # the gate script scripts/validate_master_tables.py was edited by the validation cleanup (item 23 BLIND declaration, Lotte WFY exemption): it is compared with the validation post copy, not with HEAD
    ('"data/_gold/pl_csm_amort_missing_ledger.json", "scripts/validate_master_tables.py", "scripts/validate_data_contract.py",', '"data/_gold/pl_csm_amort_missing_ledger.json", "scripts/validate_data_contract.py",'),
    ('# ------------------------------------------------------------------------------------------------ PL provenance\n',
     'chk("scripts/validate_master_tables.py: equal to the validation cleanup post copy (gate_cleanup/post_copies; this load does not touch gate scripts)", (ROOT / "scripts/validate_master_tables.py").read_bytes() == (ROOT / "data/_derived/remaining_20261022/e23_d1_d3/gate_cleanup/post_copies/validate_master_tables.py").read_bytes())\n'
     'chk("tests/fixtures/pl_breakdown_golden.json, viz fixtures: byte-equal to the pre-load backup (this load must not need a PL golden update)", all((ROOT / r).read_bytes() == (BK / r).read_bytes() for r in ("tests/fixtures/pl_breakdown_golden.json", "tests/fixtures/viz_ifrs17_panels_golden.json", "tests/fixtures/viz_csm_waterfall_golden.json")))\n'
     '# ------------------------------------------------------------------------------------------------ PL provenance\n'),
])
patch("summarize_changes.py", [
    ('BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb"\n', 'BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2"\n'),
])
patch("c13_emitter_prestate.py", [
    ("scratchpad/e23_kr0072_sim\")", "scratchpad/e23_kr0072_load2_sim\")"),
])
patch("c18_sim_vs_applied.py", [
    ("scratchpad/e23_kr0072_sim\")", "scratchpad/e23_kr0072_load2_sim\")"),
])
patch("c17_cmp_backup.py", [
    ('BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb"\n', 'BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb_load2"\n'),
])
patch("b04_backup_check.py", [
    ('BK = EV / "backup_before_apply/kr0072_kdb"\n', 'BK = EV / "backup_before_apply/kr0072_kdb_load2"\n'),
    ('MAN = json.loads((EV / "kr0072_kdb/apply_manifest_e23_kdb.json").read_text(encoding="utf-8"))\n', 'MAN = json.loads((EV / "kr0072_kdb_load2/apply_manifest_e23_kdb.json").read_text(encoding="utf-8"))\n'),
    ('ABLM = json.loads((EV / "kr0070_abl/apply_manifest_e23_abl.json").read_text(encoding="utf-8"))\n', 'ABLM = json.loads((EV / "kr0009_hyundai/apply_manifest_e23_hd.json").read_text(encoding="utf-8"))   # Hyundai manifest = predecessor state\n'
     'ABLM["after_sha256"]["tests/test_rule_coverage_manifest.py"] = hashlib.sha256((EV / "gate_cleanup/post_copies/test_rule_coverage_manifest.py").read_bytes()).hexdigest()   # the validation cleanup edited the test file after the Hyundai load\n'),
])
patch("run_tests.sh", [("O=data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb\n", "O=data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2\n")])
patch("run_tests_final.sh", [("O=data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb\n", "O=data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb_load2\n")])
for n in ("gate_overlay.py", "compare_gates.py", "run_gates.sh"):
    shutil.copyfile(OLD / n, HERE / n)
    print("copied", n)
