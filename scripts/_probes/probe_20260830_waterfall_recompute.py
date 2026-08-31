"""Read-only reproduction of build_csm_waterfall_master.main()'s per-company
logic, scoped to 3 target companies (KR0079/KR0003/KR0072), to cross-check
gold override values against a fresh raw-XML recompute using the CURRENT
(already-fixed, commit 9a067dd) extract_stages(). Does NOT call main(),
does NOT write any master/diag file -- read-only import per the ticket's
explicit allowance.
"""
import sys, json, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import waterfall_for_dir, quarter_from, META

TARGETS = ["KR0079", "KR0003", "KR0072"]

for kr in TARGETS:
    name, ticker, sb = META.get(kr, (kr, None, None))
    dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()),
                  key=lambda rd: (lambda m: (int(m.group(1)), int(m.group(2))) if m else (0,0))(re.search(r"FY(\d{4})_Q(\d)", str(rd))))
    print(f"\n===== {kr} {name} ({sb}) — {len(dirs)} raw dirs =====")
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
    for rd in dirs:
        q = quarter_from(rd)
        if not q:
            continue
        y = int(q[:4])
        anchor = None if q.endswith("4Q") else (annual_open.get(y) or annual_close.get(y - 1))
        vals, src = waterfall_for_dir(rd, name, anchor)
        vs = {k: vals.get(k) for k in range(1,7)} if vals else None
        print(f"  {q}  anchor={anchor}  src={src}")
        print(f"       vals={vs}")
