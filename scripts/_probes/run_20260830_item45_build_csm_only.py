# -*- coding: utf-8 -*-
"""Call build_root_masters.build_csm() ONLY (never main(), never build_pl(), never
build_csm_waterfall_master.py) so the freshly-edited gold overlay
(data/_gold/user_csm_cells.json) propagates into root CSM_waterfall.json.
Per ticket 20260830T0700Z's explicit instruction: individual build_csm() call + combo-diff."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_root_masters as brm

nc, nbad = brm.build_csm()
print(f"build_csm(): wrote {brm.CSM_OUT} ({nc} rows, {nbad} unit-error c-q nulled)")
