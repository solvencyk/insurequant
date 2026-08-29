# -*- coding: utf-8 -*-
"""Call build_root_masters.build_csm() ONLY (never main(), never build_pl()) to
propagate the patched csm_waterfall_master_diag.json into root CSM_waterfall.json.
Per ticket 20260830T0200Z's explicit instruction: '개별 빌더(build_csm/build_pl)만
호출하고 전후 combo-diff로 셀 손실 0을 확인한다'.
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import build_root_masters as brm

nc, nbad = brm.build_csm()
print(f"build_csm(): wrote {brm.CSM_OUT} ({nc} rows, {nbad} unit-error c-q nulled)")
