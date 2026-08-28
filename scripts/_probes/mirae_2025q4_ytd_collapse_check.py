# -*- coding: utf-8 -*-
"""Affirmative/negative check: does validate_data_contract.py's own _pl_ytd_collapse() fire
for KR0079 2025.4Q item6 against the PRE-patch backup, and NOT against the POST-patch current
PL_breakdown.json? Read-only (imports the validator module's function, doesn't run main()).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validate_master_tables import load_long  # noqa: E402
from scripts.validate_data_contract import _pl_ytd_collapse  # noqa: E402

for label, path in [
    ("PRE-patch (backup)", "PL_breakdown.json.bak_20260829_item6_nullify"),
    ("POST-patch (current)", "PL_breakdown.json"),
]:
    pl = load_long(path)
    hits = _pl_ytd_collapse(pl)
    mirae_hits = [h for h in hits if h[0] == "미래에셋생명보험"]
    print(f"{label}: total collapse hits={len(hits)}  미래에셋생명보험 hits={mirae_hits}")
