# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
led = json.loads((ROOT / "data/_gold/kics_exemption_provenance.json").read_text(encoding="utf-8"))
print("top keys:", list(led))
for e in led.get("entries", []):
    st = e.get("status")
    if st == "CONTRADICTED":
        continue
    print(f"{e.get('registry'):38s} {e.get('company')} {e.get('quarter'):8s} status={st}")
    for k in ("expected_residual", "expected_residual_alt_reading", "cells", "absent_cells", "pin_tolerance"):
        if k in e:
            print(f"     {k} = {json.dumps(e[k], ensure_ascii=False)}")
