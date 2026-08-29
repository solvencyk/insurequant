# -*- coding: utf-8 -*-
"""Directly recompute the CSM_AMORT identity residual for KR0079/미래에셋생명보험 2025.2Q
using the SAME helper functions the gate itself uses (validate_master_tables.py), to
independently confirm the ticket's claim that the residual becomes 0.00억 (tol 0.50억)."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import validate_master_tables as vmt

wf = vmt.load_long("CSM_waterfall.json")
pl_idx = vmt.load_long("PL_breakdown.json")

key = ("미래에셋생명보험", "2025.2Q")
wfm = wf.get(key)
plm = pl_idx.get(key)
print("wfm CSM상각:", wfm.get("CSM상각") if wfm else None)
print("plm 원수CSM상각:", plm.get("원수CSM상각") if plm else None)
print("plm 수재CSM상각:", plm.get("수재CSM상각") if plm else None)

rr = vmt.csm_amort_residual(plm, wfm)
print("csm_amort_residual(plm, wfm) = (resid, pl_eok, amort_eok):", rr)
if rr:
    resid, pl_eok, amort_eok = rr
    tol = vmt.csm_amort_tol(amort_eok)
    print(f"tolerance = {tol}")
    print(f"within tolerance: {abs(resid) <= tol}")

ledger = vmt.csm_amort_ledger()
entry = ledger.get("entries", {}).get(f"{key[0]}|{key[1]}")
print("ledger entry for this key (should be None now):", entry)
verdict = vmt.csm_amort_ledger_verdict(entry, rr[0] if rr else None)
print("verdict:", verdict)
