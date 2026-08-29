# -*- coding: utf-8 -*-
"""Reproduce main()'s exact 2-pass anchor logic (Pass1: annual open/close without
anchor; Pass2: emit with same-year Q4-opening anchor for Q1-3) for KR0079 ONLY,
calling waterfall_for_dir() end-to-end (POST-FIX code). Read-only -- no JSON writes,
no main()/build_root_masters.py execution. Prints the full 6-item vector per quarter
plus the coverage src tag, for comparison against the pre-fix cov file and the
ticket's raw-confirmed expected values.
"""
import sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import waterfall_for_dir, quarter_from, META

kr = "KR0079"
name = META.get(kr, (kr, None, None))[0]
dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()),
              key=lambda rd: (lambda m: (int(m.group(1)), int(m.group(2))) if m else (0, 0))(
                  re.search(r"FY(\d{4})_Q(\d)", str(rd))))

annual_open, annual_close = {}, {}
for rd in dirs:
    q = quarter_from(rd)
    if q and q.endswith("4Q"):
        av, _ = waterfall_for_dir(rd, name, None)
        if av:
            if av.get(1) is not None:
                annual_open[int(q[:4])] = av[1]
            if av.get(6) is not None:
                annual_close[int(q[:4])] = av[6]

print(f"annual_open={annual_open}")
print(f"annual_close={annual_close}")
print()

for rd in dirs:
    q = quarter_from(rd)
    if not q:
        continue
    y = int(q[:4])
    anchor = None if q.endswith("4Q") else (annual_open.get(y) or annual_close.get(y - 1))
    vals, src = waterfall_for_dir(rd, name, anchor)
    print(f"{q}: anchor={anchor} src={src}")
    print(f"      vals={vals}")
