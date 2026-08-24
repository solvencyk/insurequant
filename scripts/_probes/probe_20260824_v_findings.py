# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
rep = json.loads((ROOT / "artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
code, q = sys.argv[1], sys.argv[2]
pat = sys.argv[3] if len(sys.argv) > 3 else ""
for f in rep.get("findings", []):
    if f.get("원보험사코드") == code and f.get("공시분기") == q and pat in str(f.get("rule")):
        if f.get("status") in ("RED", "YELLOW"):
            print(f"{f['status']:6s} {f['rule']:34s} exp={f.get('expected')} act={f.get('actual')} "
                  f"diff={f.get('diff')}\n        {str(f.get('detail'))[:230]}")
