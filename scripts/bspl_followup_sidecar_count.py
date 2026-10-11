#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
side = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))
ov = json.loads((ROOT / "data/dart/viz/bs_manual_overrides.json").read_text(encoding="utf-8"))
print("sidecar cells", len(side["cells"]))
cells = ov.get("cells") if isinstance(ov, dict) and "cells" in ov else None
print("overlay keys", list(ov.keys())[:6], "cells" if cells is not None else "", len(cells) if cells is not None else "")
parts = {}
for p in sorted((ROOT / "data/_derived/bs_from_disclosure_parts").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    for k, v in (d.get("cells") or {}).items() if isinstance(d, dict) else []:
        parts.setdefault(k, []).append(p.name)
print("distinct cell keys across parts", len(parts))
missing_in_side = [k for k in parts if k not in side["cells"]]
missing_in_parts = [k for k in side["cells"] if k not in parts]
print("in parts but not in sidecar:", len(missing_in_side), missing_in_side[:5], "| in sidecar but not in parts:", len(missing_in_parts), missing_in_parts[:5])
