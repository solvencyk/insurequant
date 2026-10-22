"""Probe: which WFY_EXCEPTIONS entries are still needed?  Read-only.

For each (company, FY) in validate_master_tables.WFY_EXCEPTIONS, evaluate both consumers
(master_tables._check_plausibility WFY axis; validate_csm_continuity.check_company within-FY axis)
with the set emptied, and report whether that entry would flag.
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as V  # noqa: E402
import validate_csm_continuity as C  # noqa: E402

orig = set(V.WFY_EXCEPTIONS)
WF = sys.argv[1] if len(sys.argv) > 1 else V.WF_PATH
wf = V.load_long(WF)
C.SRC = Path(WF)
by_co, names = C.load()

V.WFY_EXCEPTIONS.clear()          # same object imported by C
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    _dup, _spike, _cont, wfy_rows, _z = V._check_plausibility(wf)
master_flag = {(co, fy) for co, fy, _ in wfy_rows}

cont_flag = set()
for co, data in by_co.items():
    for f in C.check_company(data, names.get(co)):
        if f["rule"] == "WITHIN_FY_OPENING_DRIFT":
            cont_flag.add((names[co], str(f["fy"])))
V.WFY_EXCEPTIONS.update(orig)

print(f"entries={len(orig)}")
for k in sorted(orig):
    m = k in master_flag
    c = k in cont_flag
    print(f"{k[0]:12s} FY{k[1]}  master_tables_flags={m!s:5s}  continuity_flags={c!s:5s}  -> "
          f"{'KEEP' if (m or c) else 'UNUSED (safe to remove)'}")
extra = (master_flag | cont_flag) - orig
print("flags outside the set (would be new RED if exceptions were all gone):", sorted(extra))
