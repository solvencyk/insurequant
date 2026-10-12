# -*- coding: utf-8 -*-
"""One-off: derive scripts/apply_ifrs17_bs_fix_20261012.py from scripts/bspl_followup_apply_bs_fix.py (same cell-level BS corrector, new lineage text / backup / manifest)."""
src = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/bspl_followup_apply_bs_fix.py"
dst = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/apply_ifrs17_bs_fix_20261012.py"
s = open(src, encoding="utf-8", newline="").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)
rep('"""Cell-level BS corrector for the 2026-10-11 follow-up (parser/ifrs17, inbox/parser/20261011T0900Z).',
    '"""Cell-level BS corrector for the 2026-10-12 owner-approved follow-ups (parser/ifrs17, inbox/parser/20261012T1020Z) -- Chubb item 20 on the K-IFRS basis.\n\n(Copy of scripts/bspl_followup_apply_bs_fix.py with this round\'s backup dir / manifest / lineage text; the logic is unchanged.)')
rep('Applies a spec (data/_derived/bspl_followup_20261011/*_fix_spec.json: cells with action replace | add | keep) to',
    'Applies a spec (data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_bs.json: cells with action replace | add | keep) to')
rep('data/_derived/bspl_followup_backup_20261011/<round>/.', 'data/_derived/ifrs17_owner_followups_backup_20261012/<round>/.')
rep('scripts/bspl_followup_apply_bs_fix.py --spec', 'scripts/apply_ifrs17_bs_fix_20261012.py --spec')
rep('BACKUP = ROOT / "data" / "_derived" / "bspl_followup_backup_20261011"', 'BACKUP = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012"')
rep('MANIFEST = ROOT / "data" / "_derived" / "bspl_followup_20261011" / "load_manifest_followup.json"',
    'MANIFEST = ROOT / "data" / "_derived" / "ifrs17_owner_followups_20261012" / "bs_apply_manifest.json"')
rep('f"[{stamp}] 후속(inbox/parser/20261011T0900Z, round {a.round}) -- 정정 {n_rep}칸(옛 값 guard) + 신규 {n_add}칸, "\n                         f"scripts/bspl_followup_apply_bs_fix.py 로 셀단위.',
    'f"[{stamp}] owner 승인 후속(inbox/parser/20261012T1020Z, round {a.round}) -- 정정 {n_rep}칸(옛 값 guard) + 신규 {n_add}칸, "\n                         f"scripts/apply_ifrs17_bs_fix_20261012.py 로 셀단위.')
rep('obj["_readme"] = [f"[{stamp}] 후속(inbox/parser/20261011T0900Z) 정정·신규 칸의 계보 -- scripts/bspl_followup_apply_bs_fix.py 가 쓴다. "',
    'obj["_readme"] = [f"[{stamp}] owner 승인 후속(inbox/parser/20261012T1020Z) 정정·신규 칸의 계보 -- scripts/apply_ifrs17_bs_fix_20261012.py 가 쓴다. "')
open(dst, "w", encoding="utf-8", newline="").write(s)
print("written", dst, len(s))
