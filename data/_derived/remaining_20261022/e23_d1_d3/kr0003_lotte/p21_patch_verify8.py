# -*- coding: utf-8 -*-
"""kr0003_verify.py: read the 'live master' (old values, gold) from KR0003_BASE (default: the repo root).  After the load, KR0003_BASE=<backup_before_apply/kr0003_lotte> replays the pre-load comparison."""
from pathlib import Path

p = Path("kr0003_verify.py")
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:90])
    s = s.replace(a, b)


sub('OUTTAG = os.environ.get("KR0003_OUTTAG", "")\n', 'OUTTAG = os.environ.get("KR0003_OUTTAG", "")\nBASE = Path(os.environ.get("KR0003_BASE", str(ROOT)))   # where the pre-load masters / gold files are read from (default: the repo root = before the load)\n')
sub('pl_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}',
    'pl_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((BASE / "PL_breakdown.json").read_text(encoding="utf-8"))}')
sub('csm_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}',
    'csm_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((BASE / "CSM_waterfall.json").read_text(encoding="utf-8"))}')
sub('gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))', 'gold = json.loads((BASE / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))')
sub('cgold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))', 'cgold = json.loads((BASE / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))')
sub('    say(f"  live KR0003 PL+CSM rows differing from git HEAD: {n_diff} (must be 0: nobody touched this company)")',
    '    say(f"  base masters ({BASE}) KR0003 PL+CSM rows differing from git HEAD: {n_diff} (must be 0: nobody touched this company before the load)")')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
